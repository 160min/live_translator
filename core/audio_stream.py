"""
core/audio_stream.py  (이준섭 - 2주차)

마이크 실시간 수음 -> silero-vad 발화 분할 -> STT 전사(+전공 용어 프롬프트 바이어싱)
-> TranscriptionResult 객체를 출력 큐로 전달

사용 예 (main.py 에서)
    out_q = queue.Queue()
    stt = AudioTranscriber(out_q, glossary=hint, backend="local", device="cuda")
    stt.start()                       # 모델 로딩은 이 스레드 안에서 일어남 (UI 안 멈춤)
    stt.ready_event.wait(timeout=60)  # 로딩 끝나길 기다리고 싶을 때 (선택)
    ...
    result = out_q.get()              # TranscriptionResult
    ...
    stt.stop()                        # [강의 종료] 버튼

단독 테스트 (프로젝트 루트에서)
    uv run python -m core.audio_stream                 # GPU(CUDA), 안 되면 자동 CPU
    uv run python -m core.audio_stream --device cpu
    uv run python -m core.audio_stream --backend groq
"""
# ---------------------------------------------------------------------
# [CUDA] Windows에서 pip로 설치한 NVIDIA 라이브러리(cublas, cudnn) DLL 경로 등록
# 반드시 faster_whisper / ctranslate2 / torch 를 import 하기 '전에' 실행해야 함
# ---------------------------------------------------------------------
import os


def _setup_cuda_dll_path():
    if os.name != "nt":
        return
    try:
        import importlib.util

        spec = importlib.util.find_spec("nvidia")
        if spec is None or not spec.submodule_search_locations:
            return
        for base in spec.submodule_search_locations:
            for sub in os.listdir(base):
                bin_dir = os.path.join(base, sub, "bin")
                if os.path.isdir(bin_dir):
                    os.add_dll_directory(bin_dir)
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass  # 실패해도 프로그램은 계속 (CPU 폴백이 처리)


_setup_cuda_dll_path()

import dataclasses
import io
import logging
import math
import queue
import subprocess
import threading
import time
import wave
import warnings
from collections import deque

import numpy as np
import sounddevice as sd
import torch
from silero_vad import load_silero_vad

from core.schema import GlossaryHint, TranscriptionResult

log = logging.getLogger(__name__)

# schema.py 의 TranscriptionResult 에 '실제로 있는' 필드만 채우기 위한 목록
# (README 규격과 코드가 달라도, 필드가 추가/삭제돼도 깨지지 않음)
_RESULT_FIELDS = {f.name for f in dataclasses.fields(TranscriptionResult)}

# 시끄러운 외부 라이브러리 로그/경고 줄이기
for _name in ("faster_whisper", "httpx", "httpcore", "huggingface_hub"):
    logging.getLogger(_name).setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# ---------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------
SAMPLE_RATE = 16000                # Whisper / silero 모두 16kHz
CHUNK = 512                        # silero-vad는 16kHz에서 512샘플(32ms)만 받음
CHUNK_SEC = CHUNK / SAMPLE_RATE
MAX_UTTERANCE_SEC = 30.0           # 너무 길어지면 강제로 끊음
MIN_UTTERANCE_SEC = 0.3            # 이보다 짧은 소리는 잡음으로 무시
MAX_PROMPT_CHARS = 500             # Whisper 프롬프트는 약 224토큰까지만 반영 -> 한글 기준 500자

ALLOWED_LANGS = ("ko", "en")       # 자동 구분 시 후보 언어
GROQ_NAME_TO_CODE = {"korean": "ko", "english": "en"}


# ---------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------
def gpu_status() -> str:
    """nvidia-smi로 VRAM 사용량 확인 (GPU가 실제로 쓰이는지 확인용)"""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            text=True, timeout=3,
        ).strip().splitlines()[0]
        name, used, total, util = [x.strip() for x in out.split(",")]
        return f"GPU[{name}] VRAM {used}/{total} MiB, 사용률 {util}%"
    except Exception:
        return "GPU 정보 없음 (nvidia-smi 실행 불가)"


def cuda_available() -> bool:
    """
    faster-whisper(CTranslate2)가 CUDA를 쓸 수 있는지 확인.
    ※ torch.cuda.is_available() 와는 별개. faster-whisper는 torch의 CUDA가 아니라
      CTranslate2 + cuBLAS/cuDNN DLL 이 있어야 GPU로 돈다. (VAD는 CPU로 충분)
    """
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def build_prompt(glossary: GlossaryHint | None, max_chars: int = MAX_PROMPT_CHARS) -> str | None:
    """GlossaryHint -> Whisper 힌트용 str. 없거나 비어 있으면 None (PPT 없이 시작해도 동작)"""
    if glossary is None or not glossary.keywords:
        return None
    text = glossary.to_prompt_string().strip()
    if not text:
        return None
    return text[:max_chars]


# ---------------------------------------------------------------------
# STT 백엔드 1: 로컬 faster-whisper
# transcribe(audio) -> (text, lang, confidence)
# ---------------------------------------------------------------------
class LocalWhisper:
    def __init__(self, model_size: str, device: str, language: str, prompt: str | None):
        from faster_whisper import WhisperModel  # Groq만 쓸 때는 없어도 되게 지연 import

        self.language = language
        self.prompt = prompt
        self.device = device
        compute_type = "float16" if device == "cuda" else "int8"
        log.info("[STT] faster-whisper '%s' 로딩 중 (device=%s, %s)", model_size, device, compute_type)
        log.info("[GPU] 로딩 전: %s", gpu_status())
        t0 = time.time()
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        log.info("[STT] 로딩 완료 (%.1fs)", time.time() - t0)
        log.info("[GPU] 로딩 후: %s", gpu_status())

        # 워밍업: 첫 추론은 CUDA 초기화로 느리므로 무음으로 한 번 돌려둠
        # (cuBLAS/cuDNN DLL 문제는 보통 여기서 터지므로, 호출한 쪽에서 CPU 폴백 처리)
        self.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32))
        log.info("[STT] 워밍업 완료 (device=%s)", device)

    def _detect_language(self, audio: np.ndarray) -> str:
        """한국어/영어 중 확률이 높은 쪽을 선택 (일본어/중국어 오판 방지)"""
        _, _, all_probs = self.model.detect_language(audio)
        candidates = {lang: prob for lang, prob in all_probs if lang in ALLOWED_LANGS}
        if not candidates:
            return "ko"
        return max(candidates, key=candidates.get)

    def transcribe(self, audio: np.ndarray):
        lang = self._detect_language(audio) if self.language == "auto" else self.language
        segments, _ = self.model.transcribe(
            audio,
            language=lang,
            initial_prompt=self.prompt,          # <- 전공 용어 프롬프트 바이어싱
            beam_size=1,
            vad_filter=False,                    # 이미 silero로 분할함
            condition_on_previous_text=False,
        )
        segs = list(segments)                    # 제너레이터 -> 여기서 실제 전사 발생
        text = "".join(s.text for s in segs).strip()
        confidence = 0.0
        if segs:
            confidence = math.exp(sum(s.avg_logprob for s in segs) / len(segs))
        return text, lang, confidence


# ---------------------------------------------------------------------
# STT 백엔드 2: Groq API (저사양 PC용)
# ---------------------------------------------------------------------
class GroqWhisper:
    def __init__(self, model: str, language: str, prompt: str | None):
        from groq import Groq

        key = os.environ.get("GROQ_API_KEY")
        if not key:
            # 스레드 안에서 sys.exit()를 쓰면 안 되므로 예외로 알림
            raise RuntimeError("GROQ_API_KEY 환경변수(.env)가 설정되어 있지 않습니다.")
        self.client = Groq(api_key=key)
        self.model = model
        self.language = language
        self.prompt = prompt
        log.info("[STT] Groq API 사용 (model=%s)", model)

    @staticmethod
    def _to_wav_bytes(audio: np.ndarray) -> bytes:
        pcm16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm16.tobytes())
        return buf.getvalue()

    def transcribe(self, audio: np.ndarray):
        kwargs = dict(
            file=("speech.wav", self._to_wav_bytes(audio)),
            model=self.model,
            response_format="verbose_json",
        )
        if self.language != "auto":
            kwargs["language"] = self.language
        if self.prompt:
            kwargs["prompt"] = self.prompt       # <- 전공 용어 프롬프트 바이어싱

        res = self.client.audio.transcriptions.create(**kwargs)
        text = (getattr(res, "text", "") or "").strip()
        raw_lang = (getattr(res, "language", "") or "").lower()
        lang = GROQ_NAME_TO_CODE.get(raw_lang, raw_lang or self.language)
        return text, lang, 0.0


# ---------------------------------------------------------------------
# AudioTranscriber: 마이크 -> VAD -> STT -> out_queue
# ---------------------------------------------------------------------
class AudioTranscriber(threading.Thread):
    """
    Parameters
    ----------
    out_queue : TranscriptionResult 를 넣어줄 출력 큐 (다음 단계: 번역 엔진이 get)
    glossary  : PPT에서 추출한 GlossaryHint. None 이면 힌트 없이 동작.
    backend   : "local"(faster-whisper) | "groq"
    device    : "cuda" | "cpu"  (local 백엔드용. CUDA 불가/실패 시 자동으로 CPU 전환)
    language  : "auto"(한/영 자동) | "ko" | "en"
    silence   : 발화 종료로 볼 무음 길이(초)
    threshold : VAD 음성 확률 임계값
    mic       : 입력 장치 번호 (None = 시스템 기본)

    Attributes
    ----------
    ready_event   : 모델 로딩이 끝나(또는 실패해) 수음을 시작할 준비가 되면 set 됨
    load_error    : 로딩/실행 중 치명적 에러가 났을 때 그 예외 (없으면 None)
    active_device : 실제로 사용 중인 장치 ("cuda" / "cpu" / "api") - UI 표시용
    """

    def __init__(
        self,
        out_queue: queue.Queue,
        glossary: GlossaryHint | None = None,
        backend: str = "local",
        device: str = "cuda",
        model_size: str = "small",
        groq_model: str = "whisper-large-v3-turbo",
        language: str = "auto",
        silence: float = 0.7,
        threshold: float = 0.5,
        mic: int | None = None,
    ):
        super().__init__(name="AudioTranscriber", daemon=True)
        self.out_queue = out_queue
        self.glossary = glossary
        self.prompt = build_prompt(glossary)     # 생성 시 1회 str 변환

        self.backend = backend
        self.device = device
        self.model_size = model_size
        self.groq_model = groq_model
        self.language = language
        self.silence = silence
        self.threshold = threshold
        self.mic = mic

        self.ready_event = threading.Event()
        self.load_error: Exception | None = None
        self.active_device: str | None = None

        self._stop_event = threading.Event()
        self._job_q: queue.Queue = queue.Queue()   # 수음 루프 -> STT 작업자
        self._chunk_id = 0

    # -------------------------- 외부 API --------------------------
    def stop(self):
        """[강의 종료]에서 호출. 스레드가 곧 정리되고 종료됨."""
        self._stop_event.set()

    # -------------------------- 내부 로직 --------------------------
    def _load_local(self):
        """로컬 Whisper 로딩. CUDA를 우선 시도하고, 안 되면 CPU로 폴백."""
        device = self.device
        if device == "cuda" and not cuda_available():
            log.warning("[CUDA] 사용 불가 (CTranslate2가 GPU를 못 찾음) -> CPU로 전환합니다.")
            device = "cpu"

        if device == "cuda":
            try:
                self._stt = LocalWhisper(self.model_size, "cuda", self.language, self.prompt)
                self.active_device = "cuda"
                return
            except Exception as e:
                # cublas/cudnn DLL 누락 등
                log.warning("[CUDA] GPU 로딩 실패 (%s) -> CPU로 전환합니다.", e)
                log.warning("[CUDA] 해결: uv add nvidia-cublas-cu12 nvidia-cudnn-cu12")

        self._stt = LocalWhisper(self.model_size, "cpu", self.language, self.prompt)
        self.active_device = "cpu"

    def _load_engines(self):
        """STT 엔진 + VAD 로딩 (run() 안에서 호출 -> UI 스레드를 막지 않음)"""
        if self.backend == "local":
            self._load_local()
        elif self.backend == "groq":
            self._stt = GroqWhisper(self.groq_model, self.language, self.prompt)
            self.active_device = "api"
        else:
            raise ValueError(f"알 수 없는 backend: {self.backend}")
        self._vad = load_silero_vad()   # 가벼운 모델이라 CPU로 충분

    def _stt_worker(self):
        """전사가 느려도 마이크 수음이 끊기지 않도록 분리된 처리 스레드"""
        while True:
            job = self._job_q.get()
            if job is None:
                break
            audio, t_end = job
            try:
                t0 = time.time()
                text, lang, conf = self._stt.transcribe(audio)
                infer = time.time() - t0
                if not text or self._is_prompt_echo(text):
                    log.debug("(인식된 텍스트 없음 또는 프롬프트 에코 -> 버림)")
                    continue

                values = dict(chunk_id=self._chunk_id, text=text,
                              confidence=conf, is_final=True)
                result = TranscriptionResult(
                    **{k: v for k, v in values.items() if k in _RESULT_FIELDS}
                )
                self._chunk_id += 1
                self.out_queue.put(result)
                log.info("[%s|%s] %s (추론 %.2fs | 발화종료→출력 %.2fs)",
                         lang, self.active_device, text, infer, time.time() - t_end)
                if self.active_device == "cuda":
                    log.debug("   %s", gpu_status())
            except Exception as e:
                # 한 번의 전사 오류로 전체가 죽지 않게 함
                log.exception("[STT 오류] %s", e)

    def _is_prompt_echo(self, text: str) -> bool:
        """무음/잡음 구간에서 Whisper가 프롬프트를 그대로 내뱉는 환각 방지"""
        if not self.prompt:
            return False
        t = text.strip().strip(".,!? ")
        return bool(t) and t in self.prompt

    def run(self):
        # ---- 1) 모델 로딩 ----
        try:
            self._load_engines()
        except Exception as e:
            self.load_error = e
            log.exception("[AudioTranscriber] 엔진 로딩 실패")
            self.ready_event.set()               # 대기 중인 쪽이 영원히 막히지 않게
            return

        worker = threading.Thread(target=self._stt_worker, name="STTWorker", daemon=True)
        worker.start()

        audio_q: queue.Queue = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                log.warning("[오디오 상태] %s", status)
            audio_q.put(indata[:, 0].copy())     # 무거운 일 금지: 큐에 넣기만

        silence_limit = int(self.silence / CHUNK_SEC)
        preroll = deque(maxlen=int(0.3 / CHUNK_SEC))   # 첫 음절 잘림 방지
        max_chunks = int(MAX_UTTERANCE_SEC / CHUNK_SEC)

        in_speech = False
        buffer: list = []
        silence_cnt = 0

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=CHUNK,
                device=self.mic,
                callback=callback,
            ):
                log.info("[AudioTranscriber] 준비 완료. 수음 시작 (device=%s)", self.active_device)
                self.ready_event.set()

                # ---- 2) 메인 루프: stop() 이 호출될 때까지 ----
                while not self._stop_event.is_set():
                    try:
                        chunk = audio_q.get(timeout=0.1)   # 타임아웃으로 stop 신호를 주기적으로 확인
                    except queue.Empty:
                        continue

                    prob = self._vad(torch.from_numpy(chunk), SAMPLE_RATE).item()
                    is_speech = prob >= self.threshold

                    if not in_speech:
                        preroll.append(chunk)
                        if is_speech:
                            in_speech = True
                            buffer = list(preroll)
                            silence_cnt = 0
                    else:
                        buffer.append(chunk)
                        silence_cnt = 0 if is_speech else silence_cnt + 1

                        ended = silence_cnt >= silence_limit
                        too_long = len(buffer) >= max_chunks
                        if ended or too_long:
                            t_end = time.time() - (silence_cnt * CHUNK_SEC)
                            audio = np.concatenate(buffer)
                            if len(audio) / SAMPLE_RATE >= MIN_UTTERANCE_SEC:
                                self._job_q.put((audio, t_end))
                            in_speech = False
                            buffer = []
                            silence_cnt = 0
                            preroll.clear()
                            self._vad.reset_states()
        except Exception as e:
            # 마이크 장치 오류 등 (3주차 예외 처리 대상)
            self.load_error = e
            log.exception("[AudioTranscriber] 마이크 스트림 오류")
            self.ready_event.set()
        finally:
            self._job_q.put(None)                # STT 작업자 종료 신호
            worker.join(timeout=5)
            log.info("[AudioTranscriber] 종료")


# ---------------------------------------------------------------------
# 단독 테스트:  uv run python -m core.audio_stream
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["local", "groq"], default="local")
    ap.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    ap.add_argument("--language", default="auto")
    ap.add_argument("--mic", type=int, default=None)
    ap.add_argument("--keywords", nargs="*", default=["Transformer", "역전파", "경사하강법"],
                    help="테스트용 전공 용어 (빈 값이면 힌트 없이 실행)")
    ap.add_argument("--list-devices", action="store_true")
    ap.add_argument("--debug", action="store_true", help="GPU 사용량 등 상세 로그")
    args = ap.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        raise SystemExit

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(message)s")

    hint = GlossaryHint(keywords=args.keywords, source_file="test") if args.keywords else None
    out_q: queue.Queue = queue.Queue()
    t = AudioTranscriber(out_q, glossary=hint, backend=args.backend,
                         device=args.device, language=args.language, mic=args.mic)
    t.start()
    t.ready_event.wait()
    if t.load_error:
        raise SystemExit(f"시작 실패: {t.load_error}")

    print(f"\n[사용 장치: {t.active_device}] 말씀하세요. (Ctrl+C로 종료)\n")
    try:
        while True:
            try:
                print(out_q.get(timeout=0.5))
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print("\n종료합니다.")
        t.stop()
        t.join(timeout=5)