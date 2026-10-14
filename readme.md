# 프로젝트 캔버스: 강의실 실시간 전공 특화 번역 오버레이 (On-Device Local Ver.)

---

## 1. 프로젝트 개요 (Executive Summary)

- **프로젝트명:** 전공 슬라이드 문맥 기반 로컬 실시간 강의 번역 오버레이
- **목표:** 외국인 유학생을 위해 교수자 음성을 실시간 텍스트로 변환(STT) 및 번역하여 PPT 상단에 투명 자막으로 투사하는 경량 데스크톱 애플리케이션 개발
- **핵심 가치:**

1. **0원 인프라:** 외장 GPU(RTX 4060/5060) 자원을 활용한 100% 로컬 오픈소스 구동 (API 비용 영구 배제)
2. **오탐률 극복:** 수업 전 강의 자료(PPT) 사전 분석을 통한 '전공 용어 힌트 주입(Prompt Biasing)' 파이프라인 구축
3. **수업 몰입도 유지:** 웹 수신 방식의 스마트폰 딴짓 문제를 차단하고, 화면 클릭 관통(Click-Through) 오버레이로 강의 진행 방해 원천 차단

---

## 2. 해결 과제 및 핵심 해결책 (Problem & Solution)

| 구분          | 선배 팀/기존 솔루션의 한계                                         | 본 프로젝트 해결책                                                    |
| ------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------- |
| **인식률**    | 음향 모델이 전공 용어를 일반 단어로 오탐 (예: '다형성' → '다양성') | 수업 전 PPT 텍스트 추출 → 핵심 전공 키워드를 STT 프롬프트 힌트로 주입 |
| **운영 방식** | 웹 뷰어 수신 시 학생들이 스마트폰만 보며 집중도 저하               | 교탁 빔프로젝터 투사형 최상위 투명 오버레이 단독 실행                 |
| **사용성**    | PPT 전체 화면(F5) 시 자막이 숨거나 클릭 필기를 방해                | Windows API(`WS_EX_TRANSPARENT`) 기반 마우스 클릭 관통 적용           |
| **비용/지연** | 클라우드 API 호출 시 비용 발생 및 네트워크 지연(2~5초)             | 로컬 GPU(CUDA) 가속 기반 경량 오픈소스 모델 구동 (지연 0.5초 이내)    |

---

## 3. 시스템 아키텍처 및 데이터 흐름

```
[수업 5분 전] ───> PPT 파일 로드 ───> 텍스트 추출 및 전공 용어 리스트 생성
                                             │
                                             ▼ (키워드 힌트 주입)
[실시간 수업] ───> 마이크 수음 (sounddevice)
                        │
                        ▼ (VAD 무음 감지 청킹)
                   faster-whisper (로컬 GPU STT)
                        │
                        ▼ (str: 한국어 전사 텍스트)
                   Helsinki-NLP / NLLB (로컬 GPU 번역)
                        │
                        ▼ (str: 다국어 번역 텍스트)
                   PySide6 최상위 투명 오버레이 출력

```

---

## 4. 모듈 간 데이터 인터페이스 (String Pipeline 규격)

개발 경험 및 일정 최적화를 위해 복잡한 JSON 구조 대신 **단순 문자열(String) 교환 규격**을 강제합니다.

- **규칙:** 각 모듈은 이전 단계로부터 파이썬 기본 문자열(`str`) 하나를 입력받아 처리 후 문자열(`str`) 하나만 반환합니다.

```python
# 1. PPT 파서 -> STT 모듈 (수업 전 1회 생성)
glossary_str: str = "다형성, 상속, 오버라이딩, 캡슐화, 추상화"

# 2. 오디오 STT 모듈 -> 번역 모듈 (실시간 반복)
stt_result: str = "객체지향 프로그래밍에서 다형성은 매우 중요한 개념입니다."

# 3. 번역 모듈 -> GUI 오버레이 (실시간 반복)
translated_result: str = "In object-oriented programming, polymorphism is a very important concept."

```

---

## 5. 기술 스택 (Tech Stack)

- **언어 및 런타임:** Python 3.12 (64-bit)
- **GUI 프레임워크:** PySide6 (Qt for Python)
- **오디오 캡처:** `sounddevice` (Python 3.12 윈도우 환경에서 PyAudio 빌드 에러 방지)
- **음성 활동 감지:** `silero-vad` (0.5~0.8초 무음 기준 발화 청킹)
- **로컬 STT 모델:** `faster-whisper` (`small` 모델, `device="cuda"`, `compute_type="float16"`)
- **로컬 번역 모델:** HuggingFace `transformers` (`Helsinki-NLP/opus-mt-ko-en` 또는 `facebook/nllb-200-distilled-600M`)
- **문서 파싱:** `python-pptx`, `pdfplumber`
- **하드웨어 가속:** NVIDIA CUDA 12.x + GPU 가속 PyTorch

---

## 6. 팀원 역할 분담 및 마일스톤 (R&R)

### [A 담당: 오디오 캡처 및 로컬 STT]

- **핵심 과제:** 마이크 실시간 스트림 수음 및 VAD 기반 음성 슬라이싱, `faster-whisper` CUDA 연동
- **1주 차 PoC 목표:** 마이크에 대고 말을 하다 멈추면 1초 내로 콘솔 창에 정확한 텍스트가 찍히는 독립 스크립트 작성

### [B 담당: PPT 분석 및 로컬 번역 파이프라인]

- **핵심 과제:** `python-pptx` 텍스트 추출, 전공 키워드 힌트 리스트 생성, 로컬 번역 모델 세팅
- **1주 차 PoC 목표:** 임의의 전공 PPT 파일을 넣으면 핵심 단어가 추출되고, 한국어 전사 문장이 로컬 GPU 번역기를 거쳐 영문으로 즉시 변환되는 스크립트 작성

### [C 담당: PySide6 투명 오버레이 GUI]

- **핵심 과제:** 파워포인트 전체 화면(F5) 최상위 고정, 마우스 클릭 관통(Click-Through) 윈도우 속성 처리, 문자열 렌더링
- **1주 차 PoC 목표:** PPT 슬라이드 쇼를 실행하고 마우스로 화면을 넘기거나 필기해도 가려지지 않고 뒤로 숨지 않는 반투명 자막 UI 창 구현

---

## 7. 주요 위험 관리 (Risk Management)

1. **CUDA 환경 불일치:**

- PyTorch 설치 시 반드시 공식 CUDA 휠(`cu121` 또는 `cu124`)을 사용해야 합니다.
- `pip install torch --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)` 명령어로 통일합니다.

2. **PyAudio 빌드 실패:**

- Python 3.12 환경에서는 `pyaudio`를 배제하고 `sounddevice` + `numpy` 조합만 사용합니다.

3. **윈도우 이벤트 잠김:**

- 음성 인식 및 번역 처리는 반드시 별도 스레드(`QThread` 또는 `threading.Thread`)로 분리하여 GUI 메인 루프가 멈추거나 튕기는 현상을 방지합니다.
