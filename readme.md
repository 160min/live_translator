# Live Translator

> **강의 슬라이드 문맥(Context) 기반 실시간 전공 특화 번역 오버레이**  
> _Context-Aware Real-time Lecture Translation Overlay_

## 1. 개요 (Overview)

**Live Translator**는 외국인 유학생의 강의 이해도를 높이기 위해 설계된 Windows 데스크톱 애플리케이션입니다. 교수자의 마이크 음성을 실시간으로 텍스트화(STT) 및 번역하여 강의 화면 상단에 투명 자막 형태로 투사합니다.

이 프로젝트는 기존 상용 도구 및 번역기가 가진 세 가지 한계점을 해결합니다:

1. **전공 용어 오탐:** 학술/전공 전문 용어가 일반 단어로 왜곡 인식되는 문제를 강의 자료(PPT) 사전 문맥 주입(Prompt Biasing)으로 해결
2. **수업 집중도 저하:** 학생 개인 기기(웹 뷰어) 분산 방식의 스마트폰 딴짓 유발 문제를 빔프로젝터 투사형 최상위 오버레이로 차단
3. **하드웨어 환경의 제약 극복:** 외장 GPU(NVIDIA RTX 40/50 시리즈) 연산 가속을 통한 100% 로컬 구동을 기본으로 하되, **저사양 PC 환경을 위해 클라우드 API로 즉시 전환 가능한 모듈형 아키텍처** 채택

---

## 2. 주요 기능 (Key Features)

- **전공 키워드 기반 프롬프트 바이어싱 (Context-Aware STT)**
  - 수업 전 강의 슬라이드(PPTX, PDF)를 분석해 도메인 전문 키워드 리스트를 자동 추출
  - 추출된 용어집을 STT 엔진의 프롬프트 힌트로 주입하여 전공 용어 음향 오탐 원천 차단
- **인터페이스 기반 모듈형 아키텍처 (Hardware-Adaptive Modular Design)**
  - 추상화된 STT 및 번역 엔진 인터페이스를 적용하여, 구동 환경 하드웨어 사양에 따라 처리 모듈을 자유롭게 교체 가능 (Strategy Pattern)
  - **고사양 PC (GPU O):** `faster-whisper`, `Helsinki-NLP` 기반 100% 로컬 오프라인 구동 (API 비용 0원)
  - **저사양 PC (GPU X):** Groq Whisper API, Gemini 2.5 Flash API 등 초고속 클라우드 API 모듈로 전환하여 끊김 없는 실시간 번역 지원
- **F5 전체화면 관통 투명 오버레이 (Click-Through Overlay)**
  - Windows API(`WS_EX_TRANSPARENT`)를 적용해 마우스 클릭 이벤트를 100% 뒤로 통과
  - PowerPoint 슬라이드 쇼(F5) 실행 중에도 필기, 슬라이드 넘김, 레이저 포인터 등 수업 진행 간섭 배제
- **스마트 음성 활동 감지 (Silero-VAD 기반 Chunking)**
  - 단순 타임아웃 방식이 아닌 교수자의 발화 휴지기(0.5~0.8초 무음)를 실시간 감지해 문장 단위로 자동 슬라이싱

---

## 3. 시스템 아키텍처 (System Architecture)

```text
[수업 전 준비]
  PPT / PDF 강의 파일 로드
         │
         ▼ (python-pptx / pdfplumber)
  텍스트 추출 및 전공 키워드 사전(Glossary) 구성

─────────────────────────────────────────────────────────────

[수업 중 실시간 파이프라인]
  마이크 음성 입력 (sounddevice)
         │
         ▼ (실시간 스트림 청킹)
  음성 활동 감지 (Silero-VAD)
         │
         ▼ (오디오 버퍼 + 키워드 힌트 주입)

  [ STT Engine Interface (하드웨어 사양에 따라 모듈 선택) ]
   ├─ (GPU 모드) 로컬 faster-whisper (CUDA FP16)
   └─ (API 모드) Groq Whisper-large-v3 API
         │
         ▼ (TranscriptionResult 객체 반환)

  [ Translation Engine Interface (하드웨어 사양에 따라 모듈 선택) ]
   ├─ (GPU 모드) 로컬 Helsinki-NLP opus-mt-ko-en
   └─ (API 모드) Gemini 2.5 Flash API
         │
         ▼ (SubtitlePayload 객체 반환)

  PySide6 최상위 투명 오버레이 렌더링 (Click-Through 적용)
```

---

## 4. 기술 스택 (Tech Stack)

| 구분                   | 기술 / 라이브러리               | 용도 및 선정 이유                                      |
| ---------------------- | ------------------------------- | ------------------------------------------------------ |
| **Runtime**            | Python 3.12 (64-bit)            | 비동기 처리 및 최신 AI 패키지 구동 환경                |
| **GUI Framework**      | PySide6 (Qt 6)                  | 고성능 투명 윈도우 렌더링 및 윈도우 네이티브 핸들 제어 |
| **Audio Capture**      | `sounddevice`, `numpy`          | Python 3.12 윈도우 환경에서 PyAudio 빌드 충돌 회피     |
| **Voice Activity**     | `silero-vad`                    | 고정밀 딥러닝 기반 음성 구간 검출 및 무음 분할         |
| **STT Engine**         | `faster-whisper` / `groq`       | GPU 가속 로컬 전사(small 모델) 및 저사양 PC용 API 모듈 |
| **Translation Engine** | `transformers` / `google-genai` | 로컬 오프라인 번역 및 저사양 PC용 고속 문맥 번역 API   |
| **Slide Parser**       | `python-pptx`, `pdfplumber`     | 강의 자료 내 텍스트 파싱 및 키워드 집합 추출           |
| **Acceleration**       | NVIDIA CUDA 12.x / cuDNN        | RTX 30/40/50 시리즈 외장 GPU 가속 지원                 |

---

## 5. 팀원 역할 분담 (R&R)

본 프로젝트는 3인 체제로 개발되며, 각 파트의 독립적인 모듈 개발 후 팀장 주도하에 스레드(Thread) 파이프라인을 결합하는 방식으로 진행됩니다.

- **[이준섭: 오디오 캡처 및 STT 모듈]**
  - 마이크 실시간 스트림 수음 및 VAD 기반 음성 슬라이싱
  - STT 엔진 연동을 통한 실시간 원문 텍스트(DTO) 반환

- **[김진리: PPT 분석 및 번역 파이프라인]**
  - PPT 텍스트 파싱 및 사전(Glossary) 구축
  - STT 원문을 전달받아 문맥 번역을 수행하고 최종 자막 데이터(DTO) 생성

- **[김민수: PySide6 투명 오버레이 GUI]**
  - 강의 조작용 설정 창(Config Window) 구현
  - 마우스 클릭 관통 속성이 적용된 자막 투명 창 제작 및 실시간 렌더링

- **[팀장 (김민수 겸임): 파이프라인 통합 및 아키텍처 관리]**
  - `core/schema.py` 공통 데이터 규격(DTO) 설계
  - `main.py` 기반 백그라운드 스레드 및 큐(Queue) 통신 파이프라인 결합

---

## 6. 시작 가이드 (Getting Started)

### 요구 사양 (Prerequisites)

- **OS:** Windows 10 / 11 (64-bit)
- **로컬 구동 권장 사양:** NVIDIA GeForce RTX 3060 / 4060 / 5060 이상 (VRAM 6GB 이상 권장)
- **저사양 PC 구동 시:** 환경 변수(`.env`)에 외부 STT/번역 API Key 등록 필요
- **Driver:** NVIDIA 그래픽 드라이버 최신 버전 (CUDA 12.x 지원)
- **Python:** Python 3.12

### 설치 (Installation)

1. **저장소 복제**
   ```bash
   git clone https://github.com/your-org/live-translator.git
   cd live-translator
   ```
2. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **CUDA 가속 PyTorch 설치 (필수)**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
4. **의존성 라이브러리 설치**
   ```bash
   pip install -r requirements.txt
   ```

---

## 7. 프로젝트 구조 (Directory Structure)

```text
live-translator/
├── core/
│   ├── schema.py             # [DTO] 모듈 간 통신을 위한 데이터 클래스 정의
│   ├── audio_stream.py       # 마이크 실시간 캡처 및 VAD 음성 청킹
│   ├── ppt_parser.py         # PPTX/PDF 텍스트 추출 및 전공 키워드 빌더
│   ├── engine/
│   │   ├── base.py           # STT/Translation 엔진 추상 클래스(Interface)
│   │   ├── local_engine.py   # GPU 기반 faster-whisper, transformers 구현체
│   │   └── api_engine.py     # 저사양 PC용 Groq, Gemini API 구현체
├── ui/
│   ├── overlay_window.py     # 최상위 고정 및 클릭 관통 투명 자막 위젯
│   ├── config_window.py      # 마이크, 파일, 언어, 구동 모드(Local/API) 설정 창
│   └── styles.py             # Qt QSS 스타일시트
├── tests/                    # 단위 모듈 동작 테스트 스크립트
├── requirements.txt
├── main.py                   # 애플리케이션 진입점 및 스레드 파이프라인 결합
└── README.md
```

---

## 8. 모듈 간 데이터 규격 (Interface Convention / DTO)

비동기 멀티스레드 환경의 안정성과 유연한 기능 확장을 위해, 모듈 간 데이터 교환은 단순 문자열이 아닌 파이썬 내장 `@dataclass`를 활용한 DTO(Data Transfer Object) 방식으로 통일합니다.

```python
# core/schema.py
from dataclasses import dataclass, field
import time

@dataclass
class GlossaryHint:
    """PPT에서 추출된 전공 용어 컨텍스트 데이터"""
    keywords: list[str]
    source_file: str
    extracted_at: float = field(default_factory=time.time)

    def to_prompt_string(self) -> str:
        return ", ".join(self.keywords)

@dataclass
class TranscriptionResult:
    """STT 엔진이 오디오 청크를 전사한 결과 객체"""
    chunk_id: int
    text: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0
    is_final: bool = True

@dataclass
class SubtitlePayload:
    """번역 엔진이 처리를 마치고 GUI 스레드로 넘기는 최종 렌더링 객체"""
    chunk_id: int
    original_text: str
    translated_text: str
    target_lang: str = "en"
    timestamp: float = field(default_factory=time.time)

    def to_display_text(self) -> str:
        return f"{self.original_text}\n{self.translated_text}"
```
