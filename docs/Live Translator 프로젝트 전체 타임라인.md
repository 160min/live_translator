# Live Translator 프로젝트 전체 타임라인

## [1주 차] 독립 모듈 PoC (개념 검증) 및 설계

목표: 각자 맡은 핵심 기술이 내 컴퓨터에서 에러 없이 단독으로 잘 돌아가는지 증명하기 (코드 합치기 금지)

- 팀 공통 준비
  - GitHub 레포지토리 생성 및 팀원 초대
  - 공통 데이터 규격(core/schema.py) 초안 작성 (DTO 3종 정의: GlossaryHint, TranscriptionResult, SubtitlePayload)
  - 필수 라이브러리 설치 및 개발 환경 세팅 (requirements.txt 작성)
- [이준섭] 오디오 & STT 파트 (poc_audio_stt.py)
  - sounddevice로 실시간 마이크 수음 테스트
  - silero-vad를 적용해 무음 구간 감지 시 음성 청크(Chunk) 분할 검증
  - faster-whisper (또는 API)를 거쳐 마이크 음성이 콘솔 창에 텍스트로 찍히는지 확인
- [김진리] PPT 분석 & 번역 파트 (poc_ppt_parser.py, poc_translator.py)
  - python-pptx로 전공 PPT를 읽어 키워드 사전(GlossaryHint)이 깔끔하게 추출되는 단발성 함수 검증
  - 로컬 번역 모델(Helsinki-NLP) 또는 API를 구동하고, 임의의 한국어 문장이 0.5초 이내에 영문으로 번역되는지 확인
- [김민수] GUI 프론트엔드 파트 (poc_config.py, poc_overlay.py)
  - 메인 창: "PPT 첨부", "강의 시작", "강의 종료" 버튼과 선택된 파일명/상태 라벨이 포함된 조작반 UI 뼈대 구현
  - 자막 창: F5 전체 화면을 방해하지 않고 마우스 클릭이 뒤로 통과(WS_EX_TRANSPARENT)되는 반투명 자막 오버레이 창 구현
- 1주 차 완료 기준: 각자 작성한 독립 스크립트들이 개별적으로 완벽하게 작동함을 확인하고 서로 공유.

## [2주 차] 리팩토링, 모듈화 및 스레드 통합 (Integration)

목표: 널브러진 부품들을 클래스/함수로 포장하고, 팀장(main.py)이 큐(Queue)와 스레드로 조립해 하나의 프로그램으로 구동하기

- [이준섭] STT 모듈 클래스화 (core/audio_stream.py)
  - 1주 차 PoC 코드를 threading.Thread를 상속받는 AudioTranscriber 클래스로 래핑
  - 생성자(**init**)에서 PPT 추출 결과(GlossaryHint)를 인자로 받아, STT 음성 인식 시 전공 용어 프롬프트 힌트(Prompt Biasing)로 활용하도록 반영
  - print() 대신 규격화된 TranscriptionResult 객체를 생성하여 출력 큐(Queue)로 던지도록 구현
- [김진리] PPT 파서 및 번역 모듈 클래스화 (core/ppt_parser.py, core/translator.py)
  - PPT 텍스트 파싱 로직을 [PPT 첨부] 버튼 클릭 시 1회 호출 가능한 단발성 함수(extract_keywords(file_path))로 작성
  - 번역 엔진을 전략 패턴(BaseTranslator) 기반의 로컬/API 모듈로 추상화하고, 큐를 감시하며 번역을 수행하는 TranslationEngine 스레드 워커 완성
- [김민수 / 팀장] 메인 조율 및 파이프라인 결합 (main.py)
  - PPT 첨부 버튼 연동: 메인 창(ConfigWindow)에서 파일 선택 시, B의 extract_keywords()를 1회 호출해 GlossaryHint를 메인 메모리에 즉시 저장
  - 강의 시작 버튼 연동: 저장된 GlossaryHint를 A(STT)와 B(번역) 클래스 생성 인자로 각각 전달한 뒤 스레드 가동
  - A → B → C 간 데이터 흐름을 중계할 큐(Queue) 파이프라인 연결 및 C의 자막 오버레이 창(OverlayWindow) 실시간 렌더링 검증
- 2주 차 완료 기준: PPT 첨부 시 키워드 사전이 생성되고, '강의 시작'을 누르면 PPT 전공 용어가 주입된 STT와 번역이 작동하여 투명 자막 창에 실시간으로 투사됨.

## [3주 차] 실전 테스트, 최적화 및 발표 준비

목표: 실제 강의실/발표 환경 시뮬레이션을 통한 버그 픽스 및 완성도 높이기

- 종합 테스트 및 예외 처리
  - PPT 첨부를 하지 않고 '강의 시작'을 눌렀을 때의 예외 처리(빈 사전 적용 또는 경고 팝업) 점검
  - 마이크 장치 변경 및 파일 형식 에러 핸들링 점검
  - 실제 파워포인트 슬라이드 쇼(F5)를 띄워두고 그 위에서 자막 창이 매끄럽게 오버레이되는지 최종 검증
- 하드웨어 환경별 모드 점검
  - 외장 GPU(로컬 모드) 구동 시 VRAM 점유율 및 지연 시간(Latency) 체크
  - 저사양 PC 환경 대비 .env 기반 API(Groq/Gemini) 모드 스위칭 정상 작동 여부 최종 확인
- 발표 및 시연(Demo) 리허설
  - README 최종 검수 및 라이선스 고지 확인
  - 실제 시연 시나리오 작성 (PPT 첨부 -> 전공 용어 추출 -> 마이크 발화 및 오버레이 확인)
