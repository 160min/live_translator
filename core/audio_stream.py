"""
poc_audio_stt.py  (이준섭 - 1주차 PoC)

마이크 실시간 수음 -> silero-vad로 발화 구간 분할 -> STT 전사 -> 콘솔 출력
+ 말한 언어(한국어/영어) 자동 구분 후 [한국어] / [영어] 표시

전체 흐름 (이 그림만 이해하면 코드의 80%를 이해한 겁니다)
  ┌────────┐   ┌──────────┐   ┌─────────────┐   ┌─────────────┐   ┌────────┐
  │ 마이크 │ → │ 오디오 큐 │ → │ VAD(말/무음) │ → │ STT 작업 큐  │ → │ 콘솔   │
  └────────┘   └──────────┘   └─────────────┘   └─────────────┘   └────────┘
   sounddevice   콜백이 넣음     silero-vad가      별도 스레드가      print
                                 발화 끝을 판단     Whisper로 전사

사용법
  로컬(GPU):  python poc_audio_stt.py
  로컬(CPU):  python poc_audio_stt.py --device cpu
  Groq API :  set GROQ_API_KEY=xxxx  (Windows)  /  export GROQ_API_KEY=xxxx
              python poc_audio_stt.py --backend groq
  마이크 목록: python poc_audio_stt.py --list-devices
  언어 고정:   python poc_audio_stt.py --language ko   (한국어로 고정, 자동 구분 끔)

종료: Ctrl+C
"""
# ---------------------------------------------------------------------
# 표준 라이브러리 (파이썬에 기본으로 들어있는 것들)
# ---------------------------------------------------------------------
import argparse      # 실행할 때 붙이는 옵션(--device cpu 등)을 읽어주는 도구
import io            # 파일처럼 쓸 수 있는 메모리 공간(BytesIO)을 만들 때 사용
import os            # 환경변수(GROQ_API_KEY) 읽기용
import queue         # 스레드 간에 데이터를 안전하게 주고받는 큐(줄서기 통로)
import subprocess    # nvidia-smi 같은 외부 프로그램을 실행할 때 사용
import sys           # 프로그램 종료(sys.exit), 에러 출력(sys.stderr) 등
import threading     # 동시에 두 가지 일(수음 + 전사)을 하기 위한 스레드
import time          # 시간 측정(지연시간 계산)
import wave          # WAV 오디오 파일 형식을 만들 때 사용 (Groq 전송용)
from collections import deque  # 길이가 정해진 큐. 오래된 데이터는 자동으로 밀려남

# ---------------------------------------------------------------------
# 외부 라이브러리 (pip install 로 설치한 것들)
# ---------------------------------------------------------------------
import numpy as np                       # 오디오를 숫자 배열(Array)로 다루는 도구
import sounddevice as sd                 # 마이크 입력을 받아오는 도구
import torch                             # silero-vad 모델이 돌아가는 기반(PyTorch)
from silero_vad import load_silero_vad   # "지금 사람 목소리인가?"를 판단하는 VAD 모델

# ---------------------------------------------------------------------
# 상수 (프로그램 전체에서 쓰는 고정값)
# ---------------------------------------------------------------------
SAMPLE_RATE = 16000            # 1초에 소리를 16000번 측정. Whisper/silero 모두 16kHz를 기대함
CHUNK = 512                    # 한 번에 처리할 샘플 수. silero-vad는 16kHz에서 512개(=32ms)만 받음
CHUNK_SEC = CHUNK / SAMPLE_RATE  # 청크 1개가 차지하는 시간 = 0.032초
MAX_UTTERANCE_SEC = 30.0       # 말이 너무 길어지면 강제로 끊음 (Whisper는 30초 단위로 처리)
MIN_UTTERANCE_SEC = 0.3        # 이보다 짧은 소리(기침, 키보드 소리 등)는 잡음으로 보고 무시

# Whisper가 돌려주는 언어 코드 -> 화면에 보여줄 이름
LANG_LABEL = {"ko": "한국어", "en": "영어"}
# 자동 구분 모드에서 후보로 허용할 언어 (한국어/영어 둘 중 하나로만 판정)
ALLOWED_LANGS = ("ko", "en")
# Groq API는 언어를 코드가 아니라 영어 이름("korean")으로 돌려주기 때문에 변환표가 필요함
GROQ_NAME_TO_CODE = {"korean": "ko", "english": "en"}


# ----------------------------------------------------------------------
# GPU 상태 확인 (nvidia-smi)
# 목적: "연산이 진짜 GPU에서 돌고 있나?"를 VRAM 사용량으로 눈으로 확인하기 위함
# ----------------------------------------------------------------------
def gpu_status() -> str:
    try:
        # nvidia-smi는 NVIDIA 드라이버를 설치하면 같이 깔리는 GPU 상태 조회 프로그램
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",  # 쉼표로 구분된 순수 숫자로 받기
            ],
            text=True,
            timeout=3,
        ).strip().splitlines()[0]  # GPU가 여러 개여도 첫 번째 줄(첫 GPU)만 사용
        name, used, total, util = [x.strip() for x in out.split(",")]
        return f"GPU[{name}] VRAM {used}/{total} MiB, 사용률 {util}%"
    except Exception:
        # NVIDIA 그래픽카드가 없거나 nvidia-smi가 없으면 여기로 옴 (프로그램은 계속 진행)
        return "GPU 정보 없음 (nvidia-smi 실행 불가)"


# ----------------------------------------------------------------------
# STT 백엔드 1: 내 컴퓨터에서 돌리는 faster-whisper
# 두 백엔드(Local/Groq)는 transcribe(audio) -> (텍스트, 언어코드) 로 똑같이 생겼음.
# 그래서 아래 메인 코드는 어느 쪽이든 같은 방식으로 호출할 수 있음.
# ----------------------------------------------------------------------
class LocalWhisper:
    def __init__(self, model_size: str, device: str, language: str):
        # 이 import를 함수 안에 둔 이유: Groq만 쓸 때는 faster-whisper가 없어도 실행되게 하려고
        from faster_whisper import WhisperModel

        self.language = language  # "auto"면 자동 판별, "ko"/"en"이면 그 언어로 고정
        # GPU(cuda)는 float16(빠르고 정확), CPU는 int8(가볍게 압축)이 일반적인 조합
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"[STT] faster-whisper '{model_size}' 로딩 중 (device={device}, {compute_type}) ...")
        print(f"[GPU] 로딩 전: {gpu_status()}")
        t0 = time.time()
        # 모델을 메모리(GPU면 VRAM)에 올림. 처음엔 인터넷에서 모델 파일을 내려받느라 오래 걸림
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(f"[STT] 로딩 완료 ({time.time() - t0:.1f}s)")
        print(f"[GPU] 로딩 후: {gpu_status()}")  # 로딩 전보다 VRAM이 늘었으면 GPU 사용 중

        # 워밍업: 첫 추론은 CUDA 초기화 때문에 느리므로, 1초짜리 무음으로 미리 한 번 돌려둠
        self.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32))
        print("[STT] 워밍업 완료")

    def _detect_language(self, audio: np.ndarray) -> str:
        """
        말소리를 듣고 한국어/영어 중 어느 쪽에 더 가까운지 판정한다.

        Whisper는 원래 99개 언어 중에서 고르는데, 짧은 문장이면 엉뚱한 언어
        (예: 일본어, 중국어)로 오판하기도 한다. 그래서 전체 언어별 확률 중
        'ko'와 'en'만 뽑아서 둘 중 더 높은 쪽을 선택한다.
        """
        # detect_language는 (최고확률 언어, 그 확률, [(언어, 확률), ...전체 목록]) 을 돌려줌
        _, _, all_probs = self.model.detect_language(audio)
        candidates = {lang: prob for lang, prob in all_probs if lang in ALLOWED_LANGS}
        if not candidates:
            return "ko"  # 혹시 후보가 없으면 한국어를 기본값으로
        return max(candidates, key=candidates.get)  # 확률이 가장 큰 언어를 반환

    def transcribe(self, audio: np.ndarray):
        # 언어 결정: 자동이면 위 함수로 판별, 아니면 사용자가 지정한 값을 그대로 사용
        lang = self._detect_language(audio) if self.language == "auto" else self.language

        segments, _ = self.model.transcribe(
            audio,                          # float32 numpy 배열 (-1.0 ~ 1.0, 16kHz, 모노)
            language=lang,                  # 판별된 언어로 고정해서 전사 (정확도가 올라감)
            beam_size=1,                    # 1이면 가장 빠름 (숫자가 커지면 정확하지만 느려짐)
            vad_filter=False,               # 이미 silero로 직접 분할했으므로 중복 적용 안 함
            condition_on_previous_text=False,  # 이전 문장에 끌려가서 헛소리하는 현상 방지
        )
        # segments는 '필요할 때 계산하는' 제너레이터라서, 이렇게 순회할 때 실제 전사가 일어남
        text = "".join(seg.text for seg in segments).strip()
        return text, lang


# ----------------------------------------------------------------------
# STT 백엔드 2: 인터넷으로 Groq 서버에 보내서 전사 (GPU가 약한 PC용)
# ----------------------------------------------------------------------
class GroqWhisper:
    def __init__(self, model: str, language: str):
        from groq import Groq  # Groq 쓸 때만 필요하므로 여기서 import

        key = os.environ.get("GROQ_API_KEY")  # API 키는 코드에 직접 쓰지 말고 환경변수로 관리
        if not key:
            sys.exit("GROQ_API_KEY 환경변수가 설정되어 있지 않습니다.")
        self.client = Groq(api_key=key)
        self.model = model
        self.language = language
        print(f"[STT] Groq API 사용 (model={model})")

    @staticmethod
    def _to_wav_bytes(audio: np.ndarray) -> bytes:
        """numpy 배열을 'WAV 파일 형태의 바이트'로 변환 (API는 파일 형식으로 받기 때문)"""
        # float(-1.0~1.0)을 16비트 정수(-32767~32767)로 변환. clip은 범위를 벗어난 값을 잘라냄
        pcm16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        buf = io.BytesIO()  # 디스크에 저장하지 않고 메모리 안에서 파일처럼 사용
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)           # 모노(마이크 1채널)
            wf.setsampwidth(2)           # 샘플당 2바이트 = 16비트
            wf.setframerate(SAMPLE_RATE) # 16kHz
            wf.writeframes(pcm16.tobytes())
        return buf.getvalue()

    def transcribe(self, audio: np.ndarray):
        kwargs = dict(
            file=("speech.wav", self._to_wav_bytes(audio)),  # (파일이름, 파일내용)
            model=self.model,
            # verbose_json으로 받아야 응답에 '감지된 언어'가 같이 들어있음
            response_format="verbose_json",
        )
        # 자동 모드일 때는 language를 아예 안 보내서 Groq(Whisper)가 스스로 판별하게 함
        # (참고: Groq API에서는 한/영 둘로만 제한할 수 없어서 다른 언어로 나올 수도 있음)
        if self.language != "auto":
            kwargs["language"] = self.language

        res = self.client.audio.transcriptions.create(**kwargs)
        text = (getattr(res, "text", "") or "").strip()
        # 응답의 language는 "korean" 같은 이름이라 코드("ko")로 바꿔줌. 모르는 언어면 이름 그대로 사용
        raw_lang = (getattr(res, "language", "") or "").lower()
        lang = GROQ_NAME_TO_CODE.get(raw_lang, raw_lang or self.language)
        return text, lang


# ----------------------------------------------------------------------
# STT 작업 스레드 (전사가 느려도 마이크 수음이 끊기지 않도록 분리)
# 비유: 메인 코드는 '접수 창구'(말 끊어서 접수), 이 함수는 '처리 담당자'(전사 처리)
# ----------------------------------------------------------------------
def stt_worker(stt, job_q: "queue.Queue", show_gpu: bool):
    while True:
        job = job_q.get()   # 처리할 일이 올 때까지 여기서 대기
        if job is None:     # None은 "퇴근하세요" 신호 (프로그램 종료 시 메인이 보냄)
            break
        audio, t_end = job  # 오디오 배열, 그리고 말이 끝난 시각
        try:
            t0 = time.time()
            text, lang = stt.transcribe(audio)       # 실제 전사 (+ 언어 판별)
            infer = time.time() - t0                 # 전사에만 걸린 시간
            total = time.time() - t_end              # 말이 끝난 순간 ~ 텍스트 출력까지 (체감 지연)
            if text:
                label = LANG_LABEL.get(lang, lang)   # "ko" -> "한국어" (모르는 언어면 코드 그대로)
                print(f"\n>> [{label}] {text}")
                print(f"   (음성 {len(audio) / SAMPLE_RATE:.1f}s | 추론 {infer:.2f}s | 발화종료→출력 {total:.2f}s)")
                if show_gpu:
                    print(f"   {gpu_status()}")      # 전사 직후 VRAM/GPU 사용률 확인용
            else:
                print("\n(인식된 텍스트 없음)")
        except Exception as e:
            # 전사 중 에러가 나도 프로그램 전체가 죽지 않고 다음 발화를 계속 처리
            print(f"\n[STT 오류] {e}")


# ----------------------------------------------------------------------
# 메인
# ----------------------------------------------------------------------
def main():
    # ---- 1) 실행 옵션 정의 ----
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["local", "groq"], default="local")
    ap.add_argument("--device", choices=["cuda", "cpu"], default="cuda", help="local 백엔드용")
    ap.add_argument("--model", default="small", help="faster-whisper 모델 크기")
    ap.add_argument("--groq-model", default="whisper-large-v3-turbo")
    ap.add_argument(
        "--language",
        default="auto",
        help="auto=한국어/영어 자동 구분(기본), ko 또는 en=해당 언어로 고정",
    )
    ap.add_argument("--silence", type=float, default=0.7, help="발화 종료로 판단할 무음 길이(초), 0.5~0.8 권장")
    ap.add_argument("--threshold", type=float, default=0.5, help="VAD 음성 확률 임계값 (낮을수록 민감)")
    ap.add_argument("--mic", type=int, default=None, help="입력 장치 번호")
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()

    if args.list_devices:
        print(sd.query_devices())  # 사용 가능한 마이크 목록 출력 후 종료
        return

    # ---- 2) CUDA 사용 가능 여부 사전 점검 ----
    if args.backend == "local" and args.device == "cuda":
        if not torch.cuda.is_available():
            print("[경고] CUDA를 사용할 수 없어 CPU로 전환합니다.")
            args.device = "cpu"

    # ---- 3) STT 준비 (선택한 백엔드에 따라) ----
    if args.backend == "local":
        stt = LocalWhisper(args.model, args.device, args.language)
    else:
        stt = GroqWhisper(args.groq_model, args.language)

    # ---- 4) VAD 준비 ----
    # VAD(Voice Activity Detection) = "지금 이 소리가 사람 말소리인가?"를 0~1 확률로 알려줌
    # 모델이 매우 작아서 CPU로도 충분히 빠름
    vad = load_silero_vad()

    # ---- 5) 전사 담당 스레드 시작 ----
    job_q: "queue.Queue" = queue.Queue()  # 메인 -> 전사 스레드로 일감을 넘기는 통로
    worker = threading.Thread(
        target=stt_worker,
        args=(stt, job_q, args.backend == "local" and args.device == "cuda"),
        daemon=True,  # 메인이 끝나면 같이 종료되는 스레드
    )
    worker.start()

    # ---- 6) 마이크 입력 준비 ----
    audio_q: "queue.Queue" = queue.Queue()  # 마이크 -> 메인으로 오디오 청크를 넘기는 통로

    def callback(indata, frames, time_info, status):
        # sounddevice가 청크(32ms 분량)가 쌓일 때마다 자동으로 호출해주는 함수.
        # 여기서는 무거운 일을 하면 소리가 끊기므로, 큐에 넣기만 하고 바로 끝낸다.
        if status:
            print(f"[오디오 상태] {status}", file=sys.stderr)
        audio_q.put(indata[:, 0].copy())  # [:, 0]은 첫 번째 채널만, copy는 원본 덮어쓰기 방지

    # ---- 7) 발화 분할용 변수 ----
    silence_limit = int(args.silence / CHUNK_SEC)   # "무음 몇 청크 연속이면 발화 종료?" (0.7초 ≈ 21청크)
    preroll = deque(maxlen=int(0.3 / CHUNK_SEC))    # 말 시작 직전 0.3초를 계속 보관 (첫 음절 잘림 방지)
    max_chunks = int(MAX_UTTERANCE_SEC / CHUNK_SEC) # 최대 발화 길이를 청크 개수로 환산

    in_speech = False  # 지금 말하는 중인가? (상태 플래그)
    buffer = []        # 말하는 동안의 오디오 청크를 모아두는 리스트
    silence_cnt = 0    # 말한 뒤 연속으로 무음이 몇 청크 지났는지

    print(f"\n[준비 완료] 마이크에 말씀하세요. (무음 {args.silence}s 이면 발화 종료 처리, Ctrl+C로 종료)\n")

    try:
        # with 블록 안에서 마이크 스트림이 열려 있고, 블록을 벗어나면 자동으로 닫힘
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,          # 모노
            dtype="float32",     # -1.0 ~ 1.0 범위의 실수로 받기
            blocksize=CHUNK,     # 콜백 1번에 512샘플씩
            device=args.mic,     # None이면 시스템 기본 마이크
            callback=callback,
        ):
            # ---- 8) 메인 루프: 청크를 하나씩 꺼내 '말/무음'을 판단 ----
            while True:
                chunk = audio_q.get()  # 마이크에서 새 청크가 올 때까지 대기
                # VAD에 넣으면 "이 청크가 말소리일 확률"(0~1)이 나옴
                prob = vad(torch.from_numpy(chunk), SAMPLE_RATE).item()
                is_speech = prob >= args.threshold

                if not in_speech:
                    # [상태 A: 대기 중] 아직 말이 시작되지 않음
                    preroll.append(chunk)  # 최근 0.3초를 계속 갱신하며 보관
                    if is_speech:
                        # 말이 시작됨! 직전 0.3초(preroll)부터 포함해서 녹음 시작
                        in_speech = True
                        buffer = list(preroll)
                        silence_cnt = 0
                        print("[말하는 중...]", end="\r", flush=True)
                else:
                    # [상태 B: 말하는 중] 청크를 계속 모으면서 무음이 이어지는지 감시
                    buffer.append(chunk)
                    # 말소리면 무음 카운터 리셋, 무음이면 +1 (말 중간의 짧은 쉼은 카운터가 리셋되어 무시됨)
                    silence_cnt = 0 if is_speech else silence_cnt + 1

                    ended = silence_cnt >= silence_limit   # 무음이 충분히 길었다 = 발화 종료
                    too_long = len(buffer) >= max_chunks   # 너무 길게 말함 = 강제 종료
                    if ended or too_long:
                        # 말이 실제로 끝난 시각 = 지금 - 무음이었던 시간 (지연시간 측정용)
                        t_end = time.time() - (silence_cnt * CHUNK_SEC)
                        audio = np.concatenate(buffer)  # 청크 리스트를 하나의 긴 배열로 합침
                        if len(audio) / SAMPLE_RATE >= MIN_UTTERANCE_SEC:
                            job_q.put((audio, t_end))   # 전사 스레드에 일감 전달 (기다리지 않고 바로 다음으로)
                        # 다음 발화를 위해 상태 초기화
                        in_speech = False
                        buffer = []
                        silence_cnt = 0
                        preroll.clear()
                        vad.reset_states()  # VAD 내부 기억을 비워서 이전 발화의 영향을 제거
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        job_q.put(None)  # 전사 스레드에 종료 신호 전달


# 이 파일을 직접 실행했을 때만 main()을 호출 (다른 파일에서 import하면 실행 안 됨)
if __name__ == "__main__":
    main()


#테스트 