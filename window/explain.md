# Live Translator 코드 학습 노트

## 학습 대상

- `poc_config.py`: 메인 설정 창
- `poc_overlay.py`: 실시간 자막 오버레이

## 설명 원칙

1. 원본 코드의 순서를 그대로 유지한다.
2. 코드의 모든 줄을 빠뜨리지 않고 설명한다.
3. 빈 줄과 주석도 원본 위치에 유지한다.
4. 각 코드 줄 바로 아래에 간결한 설명을 작성한다.
5. Python 기본 문법보다는 PySide6 UI 구성, Qt 스타일시트, Windows API 등 프로젝트에서 중요한 부분에 집중한다.
6. 두 파일이 어떻게 연결되어 동작하는지 마지막에 정리한다.

---

# 1. poc_config.py

### 1-1. 라이브러리 가져오기

`import sys`

- 시스템 관련 기능을 가져온다.
- 프로그램 실행과 종료에 사용한다.

`from pathlib import Path`

- 파일 경로를 객체로 다루기 위한 `Path` 클래스를 가져온다.
- 선택한 파일의 이름을 추출할 때 사용한다.

`from PySide6.QtCore import Qt`

- Qt에서 공통으로 사용하는 상수와 기능을 가져온다.
- 정렬, 창 속성, 스크롤바 정책 등에 사용한다.

`from PySide6.QtWidgets import (...)`

각 UI 구성 요소를 가져온다.

- `QApplication`: 애플리케이션 전체를 관리한다.
- `QFileDialog`: 파일 선택 창을 표시한다.
- `QFrame`: UI 영역을 구분하는 프레임이다.
- `QLabel`: 텍스트를 표시한다.
- `QMainWindow`: 메인 창의 기본 구조를 제공한다.
- `QPushButton`: 버튼을 만든다.
- `QVBoxLayout`: 위젯을 세로 방향으로 배치한다.
- `QWidget`: UI를 구성하는 기본 위젯이다.
- `QScrollArea`: 내용이 창보다 커질 때 스크롤할 수 있게 한다.

`from poc_overlay import SubtitleOverlay`

- 같은 프로젝트의 `poc_overlay.py`에서 `SubtitleOverlay` 클래스를 가져온다.
- 설정 창에서 자막 오버레이를 직접 생성하고 제어하기 위해 필요하다.

### 1-2. ConfigWindow 클래스

`class ConfigWindow(QMainWindow):`

- `ConfigWindow`라는 메인 창 클래스를 정의한다.
- `QMainWindow`를 상속하므로 기본 창 기능을 사용할 수 있다.

`def __init__(self):`

- `ConfigWindow` 객체가 생성될 때 실행되는 초기화 메서드다.

`super().__init__()`

- 부모 클래스인 `QMainWindow`의 초기화 코드를 실행한다.
- 창 객체가 정상적으로 만들어지도록 한다.

`self.selected_file: str | None = None`

- 선택한 강의 자료의 경로를 저장할 변수다.
- 처음에는 파일을 선택하지 않았으므로 `None`이다.
- `str | None`은 문자열 또는 None이 들어갈 수 있다는 타입 표시다.

`# The overlay is owned by the config window and controlled by its buttons.`

- 오버레이 객체를 설정 창이 관리하고 버튼으로 제어한다는 설명이다.

`self.overlay = SubtitleOverlay()`

- `SubtitleOverlay` 클래스로부터 새로운 오버레이 객체를 생성한다.
- 생성한 객체를 `self.overlay`에 저장한다.
- 이후 `self.overlay.show_fullscreen_overlay()`처럼 오버레이의 기능을 호출할 수 있다.

`self.setWindowTitle("Live Translator | Control Panel")`

- 메인 창의 제목 표시줄에 표시할 문구를 지정한다.

`# Allow compact windows; the content scrolls vertically when needed.`

- 창 크기를 작게 줄일 수 있고, 내용이 넘치면 세로 스크롤을 사용한다는 주석이다.

`self.setMinimumSize(340, 260)`

- 창의 최소 크기를 너비 340, 높이 260으로 제한한다.

`self.resize(540, 430)`

- 프로그램을 처음 실행했을 때의 창 크기를 540 × 430으로 설정한다.

`self._build_ui()`

- 실제 화면을 구성하는 메서드를 실행한다.

`self._apply_style()`

- 화면에 색상, 글꼴, 버튼 디자인 등을 적용하는 메서드를 실행한다.

### 1-3. UI 구성 메서드

`def _build_ui(self):`

- 메인 창 안에 들어갈 위젯과 배치를 만드는 메서드다.

`scroll = QScrollArea()`

- 스크롤 영역 객체를 생성한다.

`scroll.setObjectName("mainScroll")`

- 스크롤 영역에 `mainScroll`이라는 이름을 지정한다.
- 나중에 스타일시트에서 이 이름을 기준으로 디자인을 적용할 수 있다.

`scroll.setWidgetResizable(True)`

- 스크롤 영역의 크기에 맞춰 내부 위젯 크기를 조절하도록 한다.

`scroll.setFrameShape(QFrame.NoFrame)`

- 스크롤 영역의 기본 테두리를 없앤다.

`scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)`

- 가로 스크롤바를 항상 숨긴다.

`central = QWidget()`

- 스크롤 영역 안에 들어갈 기본 위젯을 생성한다.

`central.setObjectName("contentWidget")`

- 위젯에 `contentWidget`이라는 이름을 지정한다.

`root = QVBoxLayout(central)`

- `central` 안에 세로 배치 레이아웃을 만든다.
- 이후 추가하는 UI 요소들이 위에서 아래로 쌓인다.

`root.setContentsMargins(22, 20, 22, 20)`

- 레이아웃 내부 여백을 왼쪽 22, 위쪽 20, 오른쪽 22, 아래쪽 20으로 지정한다.

`root.setSpacing(14)`

- 세로로 배치되는 위젯 사이의 간격을 14로 설정한다.

`title = QLabel("Live Translator")`

- 제목 텍스트를 표시하는 라벨을 생성한다.

`title.setObjectName("title")`

- 라벨의 이름을 `title`로 지정한다.
- 스타일시트에서 `QLabel#title`로 선택할 수 있다.

`subtitle = QLabel("강의 실시간 번역 오버레이")`

- 제목 아래에 표시할 부제목 라벨을 생성한다.

`subtitle.setObjectName("subtitle")`

- 부제목 라벨의 이름을 지정한다.

`header = QVBoxLayout()`

- 제목과 부제목을 세로로 배치할 별도의 레이아웃을 생성한다.

`header.setSpacing(4)`

- 제목과 부제목 사이 간격을 4로 설정한다.

`header.addWidget(title)`

- 제목 라벨을 헤더 레이아웃에 추가한다.

`header.addWidget(subtitle)`

- 부제목 라벨을 헤더 레이아웃에 추가한다.

`root.addLayout(header)`

- 헤더 레이아웃 전체를 메인 레이아웃에 추가한다.

### 1-4. 강의 자료 카드

`file_card = QFrame()`

- 강의 자료 영역을 감싸는 프레임을 생성한다.

`file_card.setObjectName("card")`

- 스타일시트에서 카드 디자인을 적용할 수 있도록 이름을 지정한다.

`file_layout = QVBoxLayout(file_card)`

- 카드 내부 요소를 세로로 배치하는 레이아웃을 생성한다.

`file_layout.setContentsMargins(18, 16, 18, 16)`

- 카드 내부 여백을 설정한다.

`file_layout.setSpacing(10)`

- 카드 내부 위젯 사이 간격을 10으로 설정한다.

`file_heading = QLabel("강의 자료 (선택 사항)")`

- 강의 자료 영역의 제목을 만든다.

`file_heading.setObjectName("sectionTitle")`

- 섹션 제목 디자인을 적용하기 위한 이름이다.

`self.file_label = QLabel("첨부된 파일이 없습니다. 파일 없이도 강의를 시작할 수 있습니다.")`

- 현재 첨부된 파일 상태를 보여주는 라벨이다.
- `self.`를 붙였으므로 다른 메서드에서도 접근할 수 있다.

`self.file_label.setObjectName("fileLabel")`

- 파일 상태 라벨에 이름을 지정한다.

`self.file_label.setWordWrap(True)`

- 문장이 길어지면 자동으로 다음 줄로 넘어가게 한다.

`self.attach_button = QPushButton("＋  PPT 첨부하기")`

- PPT 첨부 버튼을 생성한다.

`self.attach_button.setObjectName("attachButton")`

- 스타일시트에서 첨부 버튼만 별도로 디자인할 수 있게 이름을 지정한다.

`self.attach_button.setMinimumHeight(44)`

- 버튼의 최소 높이를 44로 설정한다.

`self.attach_button.setToolTip("강의 자료는 첨부하지 않아도 강의를 시작할 수 있습니다.")`

- 버튼 위에 마우스를 올렸을 때 표시되는 안내 문구를 지정한다.

`self.attach_button.clicked.connect(self.on_attach_clicked)`

- 버튼이 클릭되면 `on_attach_clicked` 메서드를 실행하도록 연결한다.
- Qt의 Signal과 Slot 연결 방식이다.

`file_layout.addWidget(file_heading)`

- 카드에 강의 자료 제목을 추가한다.

`file_layout.addWidget(self.file_label)`

- 카드에 파일 상태 라벨을 추가한다.

`file_layout.addWidget(self.attach_button)`

- 카드에 첨부 버튼을 추가한다.

`root.addWidget(file_card)`

- 강의 자료 카드를 메인 레이아웃에 추가한다.

### 1-5. 강의 제어 버튼

`action_heading = QLabel("강의 제어")`

- 강의 제어 영역의 제목 라벨을 만든다.

`action_heading.setObjectName("sectionTitle")`

- 앞에서 만든 섹션 제목과 같은 디자인을 적용한다.

`root.addWidget(action_heading)`

- 메인 레이아웃에 강의 제어 제목을 추가한다.

`self.start_button = QPushButton("강의 시작")`

- 강의 시작 버튼을 생성한다.

`self.start_button.setObjectName("startButton")`

- 시작 버튼 전용 디자인을 적용하기 위한 이름이다.

`self.start_button.setMinimumHeight(48)`

- 시작 버튼의 최소 높이를 48로 설정한다.

`self.start_button.clicked.connect(self.on_start_clicked)`

- 버튼 클릭 시 `on_start_clicked`를 실행하도록 연결한다.

`self.stop_button = QPushButton("강의 종료")`

- 강의 종료 버튼을 생성한다.

`self.stop_button.setObjectName("stopButton")`

- 종료 버튼 전용 디자인을 적용하기 위한 이름이다.

`self.stop_button.setMinimumHeight(48)`

- 종료 버튼의 최소 높이를 48로 설정한다.

`self.stop_button.clicked.connect(self.on_stop_clicked)`

- 버튼 클릭 시 `on_stop_clicked`를 실행하도록 연결한다.

`root.addWidget(self.start_button)`

- 시작 버튼을 메인 레이아웃에 추가한다.

`root.addWidget(self.stop_button)`

- 종료 버튼을 메인 레이아웃에 추가한다.

### 1-6. 상태 및 하단 안내 문구

`self.status_label = QLabel("상태: 대기 중")`

- 현재 프로그램 상태를 표시하는 라벨을 생성한다.

`self.status_label.setObjectName("status")`

- 상태 라벨에 스타일을 적용하기 위한 이름이다.

`root.addWidget(self.status_label)`

- 상태 라벨을 메인 레이아웃에 추가한다.

`note = QLabel("Week 1 PoC · PPT 첨부는 선택 사항입니다")`

- 하단 안내 문구를 생성한다.

`note.setObjectName("footer")`

- 하단 안내 문구 전용 스타일을 적용하기 위한 이름이다.

`root.addWidget(note)`

- 안내 문구를 메인 레이아웃에 추가한다.

`scroll.setWidget(central)`

- 지금까지 만든 `central` 위젯을 스크롤 영역의 내부 위젯으로 지정한다.

`self.setCentralWidget(scroll)`

- 메인 창의 중앙 영역에 스크롤 영역을 배치한다.

### 1-7. 스타일 적용

`def _apply_style(self):`

- 메인 창 전체의 디자인을 설정하는 메서드다.

`self.setStyleSheet("""`

- Qt 스타일시트(QSS)를 적용한다.
- 웹 개발의 CSS와 문법이 상당히 비슷하다.
- 별도 디자인 툴이 아니라 코드로 작성하는 스타일 설정이다.

`QMainWindow, QWidget {`

- 모든 `QMainWindow`와 `QWidget`에 공통 스타일을 적용한다.

`background-color: #111827;`

- 배경색을 짙은 남색 계열로 설정한다.

`color: #F9FAFB;`

- 기본 글자색을 밝은 흰색으로 설정한다.

`font-family: "Malgun Gothic", "맑은 고딕", sans-serif;`

- 글꼴을 맑은 고딕으로 설정한다.
- 해당 글꼴이 없으면 일반 sans-serif 계열 글꼴을 사용한다.

`font-size: 10pt;`

- 기본 글자 크기를 10pt로 설정한다.

`}`

- 공통 스타일 규칙을 끝낸다.

`QScrollArea#mainScroll {`

- 이름이 `mainScroll`인 QScrollArea에만 적용할 스타일을 시작한다.

`border: none;`

- 테두리를 제거한다.

`background-color: #111827;`

- 배경색을 메인 창과 동일하게 설정한다.

`}`

`QLabel#title {`

- 이름이 `title`인 QLabel에 적용할 스타일을 시작한다.

`font-size: 21pt;`

- 제목 글자 크기를 21pt로 설정한다.

`font-weight: 700;`

- 글자 굵기를 굵게 설정한다.

`color: #F9FAFB;`

- 제목 글자색을 밝은 흰색으로 설정한다.

`}`

`QLabel#subtitle {`

- 부제목 라벨의 스타일을 시작한다.

`color: #9CA3AF;`

- 부제목을 회색으로 표시한다.

`font-size: 10pt;`

- 글자 크기를 10pt로 설정한다.

`}`

`QFrame#card {`

- 이름이 `card`인 QFrame의 스타일을 시작한다.

`background-color: #1F2937;`

- 카드 배경색을 지정한다.

`border: 1px solid #374151;`

- 1픽셀 두께의 실선 테두리를 적용한다.

`border-radius: 12px;`

- 모서리를 12픽셀 둥글게 만든다.

`}`

`QLabel#sectionTitle {`

- 섹션 제목의 스타일을 시작한다.

`color: #E5E7EB;`

- 글자색을 지정한다.

`font-size: 11pt;`

- 글자 크기를 지정한다.

`font-weight: 700;`

- 글자를 굵게 표시한다.

`}`

`QLabel#fileLabel {`

- 파일 상태 라벨의 스타일을 시작한다.

`color: #D1D5DB;`

- 글자색을 연한 회색으로 설정한다.

`padding: 5px 0;`

- 위아래에 5픽셀 여백을 준다.
- 좌우 여백은 0이다.

`}`

`QPushButton {`

- 모든 버튼에 공통으로 적용할 스타일을 시작한다.

`border: none;`

- 기본 테두리를 제거한다.

`border-radius: 8px;`

- 버튼 모서리를 둥글게 만든다.

`padding: 9px 12px;`

- 버튼 안쪽에 위아래 9픽셀, 좌우 12픽셀 여백을 준다.

`font-weight: 600;`

- 버튼 글자를 약간 굵게 표시한다.

`}`

`QPushButton:hover {`

- 마우스 포인터가 버튼 위에 올라갔을 때의 스타일을 지정한다.

`border: 1px solid #93C5FD;`

- 연한 파란색 테두리를 표시한다.

`}`

`QPushButton#attachButton {`

- 첨부 버튼만의 스타일을 시작한다.

`background-color: #374151;`

- 버튼 배경색을 설정한다.

`color: #F9FAFB;`

- 글자색을 흰색으로 설정한다.

`text-align: left;`

- 버튼 안의 텍스트를 왼쪽 정렬한다.

`border: 1px solid #4B5563;`

- 버튼에 테두리를 적용한다.

`}`

`QPushButton#attachButton:hover {`

- 첨부 버튼에 마우스를 올렸을 때의 스타일이다.

`background-color: #4B5563;`

- 배경색을 조금 밝게 변경한다.

`border: 1px solid #60A5FA;`

- 파란색 테두리를 표시한다.

`}`

`QPushButton#startButton {`

- 시작 버튼 전용 스타일을 시작한다.

`background-color: #2563EB;`

- 파란색 배경을 적용한다.

`color: white;`

- 글자를 흰색으로 표시한다.

`font-size: 11pt;`

- 글자 크기를 11pt로 설정한다.

`}`

`QPushButton#startButton:hover {`

- 시작 버튼에 마우스를 올렸을 때의 스타일이다.

`background-color: #1D4ED8;`

- 배경색을 조금 더 진한 파란색으로 변경한다.

`}`

`QPushButton#stopButton {`

- 종료 버튼 전용 스타일을 시작한다.

`background-color: #374151;`

- 어두운 회색 배경을 적용한다.

`color: #FCA5A5;`

- 글자색을 연한 빨간색으로 지정한다.

`font-size: 11pt;`

- 글자 크기를 11pt로 설정한다.

`}`

`QPushButton#stopButton:hover {`

- 종료 버튼에 마우스를 올렸을 때의 스타일이다.

`background-color: #4B5563;`

- 배경색을 조금 밝게 변경한다.

`}`

`QLabel#status {`

- 상태 라벨 전용 스타일을 시작한다.

`color: #93C5FD;`

- 글자를 연한 파란색으로 표시한다.

`padding-top: 4px;`

- 위쪽에 4픽셀 여백을 준다.

`}`

`QLabel#footer {`

- 하단 안내 문구 전용 스타일을 시작한다.

`color: #6B7280;`

- 글자색을 어두운 회색으로 설정한다.

`font-size: 8pt;`

- 글자 크기를 8pt로 설정한다.

`padding-top: 4px;`

- 위쪽에 4픽셀 여백을 준다.

`}`

`""")`

- 스타일시트 문자열을 끝내고 `setStyleSheet()`에 전달한다.
- 여기까지 작성한 QSS가 실제 UI에 적용된다.

### 1-8. PPT 첨부 기능

`def on_attach_clicked(self):`

- PPT 첨부 버튼을 클릭했을 때 실행되는 메서드다.

`file_path, _ = QFileDialog.getOpenFileName(...)`

- 파일 열기 대화상자를 표시한다.
- 선택한 파일 경로를 `file_path`에 저장한다.
- 두 번째 반환값은 파일 형식 필터이므로 `_`에 담아 사용하지 않는다.

`self.selected_file = file_path`

- 선택한 파일의 전체 경로를 객체 변수에 저장한다.

`self.file_label.setText(f"첨부됨: {Path(file_path).name}")`

- 파일 상태 라벨을 선택한 파일 이름으로 변경한다.
- `Path(file_path).name`은 전체 경로에서 파일명만 추출한다.

`print(f"[CONFIG] 파일 첨부: {file_path}", flush=True)`

- 선택한 파일 경로를 콘솔에 출력한다.
- `flush=True`는 출력 버퍼를 바로 비우도록 한다.

### 1-9. 강의 시작 기능

`def on_start_clicked(self):`

- 강의 시작 버튼을 눌렀을 때 실행된다.

`print("시작 버튼 눌림", flush=True)`

- 버튼 클릭 여부를 콘솔에 출력한다.

`if self.selected_file:`

- 파일이 선택되어 있는지 확인한다.

`print(f"[CONFIG] 선택된 강의 자료: {self.selected_file}", flush=True)`

- 파일이 선택되어 있으면 해당 경로를 출력한다.

`else:`

- 파일이 선택되지 않은 경우 실행되는 분기다.

`print("[CONFIG] 강의 자료 없이 시작합니다.", flush=True)`

- 파일 없이 시작한다는 메시지를 출력한다.

`self.overlay.show_fullscreen_overlay()`

- 오버레이를 전체 화면 크기로 표시한다.

`self.status_label.setText("상태: 강의 진행 중")`

- 메인 창의 상태 표시를 강의 진행 중으로 변경한다.

`print("[CONFIG] 자막 오버레이 표시", flush=True)`

- 오버레이가 표시되었다는 로그를 출력한다.

### 1-10. 강의 종료 기능

`def on_stop_clicked(self):`

- 강의 종료 버튼을 눌렀을 때 실행된다.

`print("종료 버튼 눌림", flush=True)`

- 종료 버튼 클릭 로그를 출력한다.

`self.overlay.hide()`

- 오버레이를 화면에서 숨긴다.
- 객체 자체를 삭제하는 것은 아니다.

`self.status_label.setText("상태: 대기 중")`

- 상태 표시를 대기 중으로 변경한다.

`print("[CONFIG] 자막 오버레이 숨김", flush=True)`

- 오버레이가 숨겨졌다는 로그를 출력한다.

### 1-11. 창 종료 처리

`def closeEvent(self, event):`

- 사용자가 창의 X 버튼을 누르는 등 창을 닫으려고 할 때 호출되는 이벤트 메서드다.

`self.overlay.close()`

- 설정 창과 함께 오버레이도 닫는다.

`if hasattr(self.overlay, "unregister_exit_hotkey"):`

- 오버레이 객체에 `unregister_exit_hotkey`라는 메서드가 존재하는지 확인한다.

`self.overlay.unregister_exit_hotkey()`

- 등록했던 전역 종료 단축키를 해제한다.

`event.accept()`

- 창 종료를 허용한다.

### 1-12. 프로그램 실행 부분

`def main():`

- 프로그램의 시작 절차를 모아 놓은 함수다.

`app = QApplication(sys.argv)`

- Qt 애플리케이션 객체를 생성한다.
- `sys.argv`는 실행 시 전달된 명령행 인자다.

`app.setApplicationName("Live Translator")`

- 애플리케이션 이름을 지정한다.

`window = ConfigWindow()`

- 메인 설정 창 객체를 생성한다.
- 이때 `ConfigWindow.__init__()`이 실행된다.

`window.show()`

- 설정 창을 화면에 표시한다.

`sys.exit(app.exec())`

- Qt 이벤트 루프를 시작한다.
- 버튼 클릭, 창 닫기 등의 이벤트를 계속 처리한다.
- 프로그램 종료 시 종료 코드를 운영체제에 전달한다.

`if __name__ == "__main__":`

- 이 파일을 직접 실행했는지 확인한다.
- 다른 파일에서 import한 경우에는 이 조건이 거짓이 된다.

`main()`

- 직접 실행한 경우 프로그램의 시작 함수인 `main()`을 호출한다.

---

# 2. poc_overlay.py

다음 부분에서는 오버레이 창 자체를 다룬다.

특히 Windows API를 이용한 클릭 통과 기능과 화면 최상단 표시 기능이 중요하다.

※ 이 파일은 다음 순서로 설명한다.

1. 모듈 설명 문자열과 라이브러리 import
2. Windows 확장 창 스타일 상수
3. `enable_click_through()` 함수
4. `SubtitleOverlay` 클래스와 UI 구성
5. 시스템 트레이 아이콘
6. 자막 변경 및 초기화
7. 창 표시 이벤트와 Windows 스타일 적용
8. 전체 화면 표시
9. 전역 단축키 등록 및 해제
10. `main()`과 독립 실행 구조

---

# 3. 두 파일의 연결 구조

`poc_config.py`가 메인 설정 창이고, `poc_overlay.py`가 실제 자막을 보여주는 창이다.

실행 흐름은 다음과 같다.

1. `main()`에서 `QApplication` 생성
2. `ConfigWindow()` 생성
3. `ConfigWindow.__init__()`에서 `SubtitleOverlay()` 생성
4. 사용자가 강의 시작 버튼 클릭
5. `on_start_clicked()` 실행
6. `self.overlay.show_fullscreen_overlay()` 호출
7. 오버레이 창 표시
8. 사용자가 강의 종료 버튼 클릭
9. `self.overlay.hide()` 실행
10. 오버레이 창 숨김

현재 코드는 UI와 오버레이 표시를 확인하기 위한 PoC다. 실제 음성 인식(STT), 번역, 자막 데이터 전달은 아직 연결되어 있지 않다.

# Live Translator — poc_overlay.py 코드 설명

## 1. 파일의 역할

`poc_overlay.py`는 번역 자막을 화면 위에 표시하는 오버레이 창을 담당한다.

주요 기능은 다음과 같다.

- 화면 전체 크기의 투명한 창 생성
- 다른 프로그램보다 위에 오버레이 표시
- 마우스 클릭을 오버레이 뒤쪽 프로그램으로 통과
- 원문과 번역문 표시
- 시스템 트레이 아이콘 제공
- Ctrl + Shift + Q 종료 단축키 지원
- 설정 창에서 호출할 수 있는 오버레이 메서드 제공

---

## 2. 모듈 설명 문자열

```python
"""
Live Translator - Week 1 PoC
Transparent, always-on-top, click-through subtitle overlay.

This module can be run standalone for overlay testing, or imported by
poc_config.py so the config window can show/hide the overlay.
"""
```

- `"""`: 여러 줄 문자열을 시작한다.
- `Live Translator - Week 1 PoC`: 이 모듈이 Live Translator의 1주 차 개념 검증용 코드라는 설명이다.
- `Transparent, always-on-top, click-through subtitle overlay.`: 투명하고, 항상 위에 표시되며, 마우스 클릭을 통과시키는 자막 오버레이라는 뜻이다.
- `This module can be run standalone...`: 이 파일을 단독 실행해 테스트할 수도 있다는 설명이다.
- `poc_config.py`: 메인 설정 창에서 이 파일의 클래스를 가져와 오버레이를 표시하거나 숨길 수도 있다는 의미다.
- 마지막 `"""`: 모듈 설명 문자열을 끝낸다.

이 문자열은 모듈의 docstring이다. 코드 실행 명령이 아니라 모듈의 목적을 설명하는 문서 역할을 한다.

---

## 3. 라이브러리 가져오기

```python
import ctypes
```

- Python에서 C 언어 기반 라이브러리의 함수와 자료형을 호출할 수 있게 해준다.
- 여기서는 Windows API인 `user32.dll`의 함수를 호출하기 위해 사용한다.
- 클릭 통과 설정, 창 위치 조정, 전역 단축키 등록 등에 필요하다.

```python
import ctypes.wintypes
```

- Windows API에서 사용하는 자료형을 제공한다.
- 예를 들어 `HWND`, `MSG` 등이 있다.
- Windows API 함수에 전달할 인자의 자료형을 정확히 지정할 때 사용한다.

```python
import sys
```

- 현재 Python 실행 환경의 정보를 제공한다.
- 여기서는 `sys.platform`을 이용해 Windows에서 실행 중인지 확인한다.
- `sys.exit()`로 프로그램을 종료할 때도 사용한다.

```python
from PySide6.QtCore import Qt, QTimer
```

- `Qt`: 창의 속성, 정렬, 배경 설정 등 Qt에서 사용하는 상수와 기능이다.
- `QTimer`: 일정 시간마다 함수를 실행하거나 지정한 시간 뒤에 함수를 실행하는 타이머 객체다.
- 이 코드에서는 창 표시 직후 Windows 스타일을 적용하거나 단축키 메시지를 주기적으로 확인할 때 사용한다.

```python
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMenu,
    QSystemTrayIcon,
    QStyle,
    QVBoxLayout,
    QWidget,
)
```

각 UI 요소의 역할은 다음과 같다.

- `QApplication`: Qt 애플리케이션 전체와 이벤트 루프를 관리한다.
- `QFrame`: 자막을 감싸는 패널을 만든다.
- `QLabel`: 원문과 번역문을 표시한다.
- `QMenu`: 시스템 트레이 아이콘을 우클릭했을 때 나오는 메뉴를 만든다.
- `QSystemTrayIcon`: Windows 작업 표시줄 알림 영역에 아이콘을 표시한다.
- `QStyle`: 운영체제의 기본 아이콘 등을 가져올 수 있다.
- `QVBoxLayout`: 위젯을 세로로 배치한다.
- `QWidget`: 오버레이 창의 기본 클래스다.

---

## 4. Windows 확장 창 스타일 상수

이 부분은 Windows API에 전달할 숫자 상수를 정의한다.

```python
# Windows extended window styles
```

- 아래 상수들이 Windows의 확장 창 스타일과 관련 있다는 주석이다.

```python
GWL_EXSTYLE = -20
```

- Windows API에서 창의 확장 스타일을 가져오거나 변경할 때 사용하는 인덱스다.
- `GetWindowLongPtrW()`와 `SetWindowLongPtrW()`에 전달한다.
- 일반 창 스타일이 아니라 확장 창 스타일을 대상으로 한다.

```python
WS_EX_TRANSPARENT = 0x00000020
```

- 확장 창 스타일 중 투명 관련 속성이다.
- 이 코드에서는 다른 확장 스타일과 함께 적용해 마우스 입력이 오버레이를 통과하도록 하는 데 사용한다.
- 실제 클릭 통과 동작은 Windows의 창 스타일 조합과 창 구성에 영향을 받으므로 실행 환경에서 확인해야 한다.

```python
WS_EX_LAYERED = 0x00080000
```

- 레이어드 창 스타일이다.
- 창의 투명도나 알파 합성 같은 기능을 사용할 수 있도록 한다.
- 이 오버레이의 투명한 배경 표현과 관련된다.

```python
WS_EX_TOOLWINDOW = 0x00000080
```

- 도구 창 스타일이다.
- 일반적인 앱 창과 다르게 작업 표시줄이나 Alt+Tab 목록에 나타나는 방식을 조정한다.
- 오버레이를 일반적인 독립 앱 창처럼 보이지 않게 하는 데 사용한다.

```python
WS_EX_NOACTIVATE = 0x08000000
```

- 창이 활성화되는 것을 방지하는 스타일이다.
- 오버레이가 나타나더라도 사용자가 작업 중인 PowerPoint 등의 프로그램이 포커스를 잃지 않도록 하는 목적이다.

---

## 5. Windows 창 위치 관련 상수

```python
# Windows positioning constants
```

- 아래 상수들이 Windows 창 위치와 상태를 조정하는 데 사용된다는 주석이다.

```python
HWND_TOPMOST = -1
```

- 창을 항상 위에 표시하도록 지정할 때 사용하는 값이다.
- `SetWindowPos()`의 두 번째 인자로 전달한다.

```python
SWP_NOMOVE = 0x0002
```

- 창의 위치를 변경하지 않도록 지정한다.

```python
SWP_NOSIZE = 0x0001
```

- 창의 크기를 변경하지 않도록 지정한다.

```python
SWP_NOACTIVATE = 0x0010
```

- 창 위치나 스타일을 변경해도 해당 창을 활성화하지 않도록 지정한다.

```python
SWP_FRAMECHANGED = 0x0020
```

- 창 스타일이 변경되었음을 Windows에 알리고 창 프레임을 다시 계산하도록 요청한다.
- 확장 스타일 변경 사항을 반영하기 위해 사용한다.

---

## 6. 전역 단축키 상수

```python
# Global hotkey: Ctrl + Shift + Q
```

- 전역 단축키가 Ctrl + Shift + Q라는 설명이다.
- 전역 단축키는 오버레이 창이 현재 활성 창이 아니어도 입력을 감지할 수 있는 단축키다.

```python
MOD_CONTROL = 0x0002
```

- Ctrl 키를 나타내는 Windows 단축키 modifier 값이다.

```python
MOD_SHIFT = 0x0004
```

- Shift 키를 나타내는 modifier 값이다.

```python
WM_HOTKEY = 0x0312
```

- Windows가 등록된 전역 단축키 입력을 알릴 때 사용하는 메시지 식별자다.
- 메시지 큐에서 이 값으로 단축키 메시지를 확인한다.

```python
HOTKEY_ID = 1
```

- 등록할 단축키에 부여하는 식별 번호다.
- 나중에 어떤 단축키가 눌렸는지 구분할 때 사용한다.

```python
VK_Q = 0x51
```

- 키보드의 Q 키를 나타내는 가상 키 코드다.
- Ctrl, Shift와 조합해 Ctrl + Shift + Q를 구성한다.

---

## 7. 클릭 통과 기능: enable_click_through()

```python
def enable_click_through(hwnd: int):
```

- Windows 창에 클릭 통과 스타일을 적용하는 함수다.
- `hwnd`는 Windows가 각 창에 부여하는 고유한 창 핸들이다.
- `int`는 이 함수에 정수 형태의 창 핸들을 전달한다는 타입 힌트다.

```python
"""Apply native Windows styles so mouse input passes through this window."""
```

- Windows의 네이티브 창 스타일을 적용해 마우스 입력이 이 창을 통과하도록 한다는 설명이다.

```python
user32 = ctypes.windll.user32
```

- Windows의 `user32.dll`에 접근한다.
- `user32.dll`은 창 생성, 창 위치, 메시지 처리, 키보드 입력 등 Windows GUI 관련 기능을 제공한다.
- 이후 `user32.GetWindowLongPtrW()`와 같은 함수를 호출할 수 있다.

```python
get_style = user32.GetWindowLongPtrW
```

- 창의 지정된 스타일 값을 읽는 Windows API 함수를 변수에 담는다.
- 여기서는 확장 창 스타일을 읽는 데 사용한다.

```python
set_style = user32.SetWindowLongPtrW
```

- 창의 지정된 스타일 값을 변경하는 Windows API 함수를 변수에 담는다.

```python
get_style.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
```

- `GetWindowLongPtrW()`에 전달하는 인자들의 자료형을 지정한다.
- 첫 번째 인자는 창 핸들 `HWND`다.
- 두 번째 인자는 스타일 인덱스인 정수다.

```python
get_style.restype = ctypes.c_ssize_t
```

- 함수의 반환 자료형을 지정한다.
- 창 스타일 값이 포인터 크기 정수로 반환되도록 한다.

```python
set_style.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
```

- `SetWindowLongPtrW()`에 전달하는 인자 자료형을 지정한다.
- 첫 번째: 대상 창 핸들
- 두 번째: 변경할 스타일의 인덱스
- 세 번째: 적용할 스타일 값

```python
set_style.restype = ctypes.c_ssize_t
```

- 함수의 반환 자료형을 지정한다.

```python
ex_style = get_style(hwnd, GWL_EXSTYLE)
```

- 전달받은 창 핸들의 현재 확장 스타일을 읽는다.
- `GWL_EXSTYLE`을 전달했으므로 확장 스타일을 가져온다.

```python
ex_style |= (
    WS_EX_LAYERED
    | WS_EX_TRANSPARENT
    | WS_EX_TOOLWINDOW
    | WS_EX_NOACTIVATE
)
```

- 기존 확장 스타일에 필요한 스타일을 추가한다.
- `|`는 비트 OR 연산자다.
- `|=`는 기존 변수에 비트 OR 결과를 다시 저장하는 연산이다.
- 기존 스타일을 통째로 덮어쓰는 대신 필요한 비트를 추가한다.

각 스타일의 목적은 다음과 같다.

- `WS_EX_LAYERED`: 레이어드 창으로 설정한다.
- `WS_EX_TRANSPARENT`: 클릭 통과 설정에 사용한다.
- `WS_EX_TOOLWINDOW`: 도구 창 스타일을 적용한다.
- `WS_EX_NOACTIVATE`: 창이 활성화되지 않도록 한다.

```python
set_style(hwnd, GWL_EXSTYLE, ex_style)
```

- 변경된 확장 스타일을 실제 Windows 창에 적용한다.

```python
user32.SetWindowPos(
    hwnd,
    HWND_TOPMOST,
    0, 0, 0, 0,
    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
)
```

- Windows API를 이용해 창의 표시 순서와 상태를 갱신한다.
- 첫 번째 인자 `hwnd`: 대상 창이다.
- 두 번째 인자 `HWND_TOPMOST`: 항상 위에 표시한다.
- `0, 0, 0, 0`: 좌표와 크기 인자다. 다만 아래 플래그 때문에 위치와 크기는 변경하지 않는다.
- `SWP_NOMOVE`: 위치를 유지한다.
- `SWP_NOSIZE`: 크기를 유지한다.
- `SWP_NOACTIVATE`: 창을 활성화하지 않는다.
- `SWP_FRAMECHANGED`: 변경된 스타일을 반영하도록 한다.

이 함수의 핵심은 **Qt에서 만든 창에 Windows API를 이용해 네이티브 확장 스타일을 추가하는 것**이다.

---

## 8. SubtitleOverlay 클래스

```python
class SubtitleOverlay(QWidget):
```

- `SubtitleOverlay`라는 오버레이 클래스를 정의한다.
- `QWidget`을 상속하므로 Qt 창의 기본 기능을 사용할 수 있다.
- `poc_config.py`에서 이 클래스를 가져와 사용한다.

```python
def __init__(self):
```

- 오버레이 객체가 생성될 때 실행되는 초기화 메서드다.

```python
super().__init__()
```

- 부모 클래스인 `QWidget`의 초기화 코드를 실행한다.

```python
self.setWindowTitle("Live Translator Overlay")
```

- 오버레이 창의 제목을 지정한다.

```python
self.setWindowFlags(
    Qt.WindowType.FramelessWindowHint
    | Qt.WindowType.WindowStaysOnTopHint
    | Qt.WindowType.Tool
)
```

- 오버레이 창의 동작 방식을 지정한다.
- `FramelessWindowHint`: 제목 표시줄과 기본 테두리를 제거한다.
- `WindowStaysOnTopHint`: 다른 일반 창보다 위에 표시하도록 요청한다.
- `Tool`: 도구 창 형태로 표시한다.
- `|`를 사용해 여러 창 속성을 동시에 적용한다.

```python
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
```

- 위젯 배경을 투명하게 처리할 수 있도록 설정한다.
- `True`는 해당 속성을 활성화한다.
- 자막 패널 외부 영역을 투명하게 표현하는 데 사용한다.

```python
self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
```

- 창이 표시될 때 활성 창으로 바뀌지 않도록 요청한다.
- 사용자가 보고 있던 PowerPoint 등의 창에 포커스를 유지하려는 목적이다.

```python
self._hotkey_registered = False
```

- 전역 단축키가 등록되어 있는지를 기록하는 변수다.
- 처음에는 등록하지 않았으므로 `False`다.
- 중복 등록이나 불필요한 해제를 방지하는 데 사용한다.

```python
self._build_ui()
```

- 자막 오버레이의 내부 UI를 구성한다.

```python
self._create_tray_icon()
```

- Windows 시스템 트레이 아이콘과 메뉴를 생성한다.

---

## 9. 오버레이 UI 구성: \_build_ui()

```python
def _build_ui(self):
```

- 오버레이 창 안에 자막 패널과 텍스트 라벨을 배치하는 메서드다.

```python
root = QVBoxLayout(self)
```

- 현재 오버레이 창인 `self`에 세로 레이아웃을 만든다.
- 이후 추가하는 요소를 위에서 아래 방향으로 배치한다.

```python
root.setContentsMargins(80, 0, 80, 55)
```

- 레이아웃 내부 여백을 설정한다.
- 왼쪽 80, 위쪽 0, 오른쪽 80, 아래쪽 55다.
- 좌우 여백은 자막 패널이 화면 가장자리와 너무 가까워지지 않도록 한다.
- 아래쪽 여백은 패널을 화면 하단에서 조금 위로 올리는 데 영향을 준다.

```python
root.addStretch(1)
```

- 레이아웃에 늘어날 수 있는 빈 공간을 추가한다.
- 남는 세로 공간을 위쪽에서 차지하게 해 자막 패널이 화면 아래쪽에 위치하도록 한다.
- `1`은 다른 stretch 항목과 비교할 때 사용하는 비율이다.

```python
self.panel = QFrame()
```

- 자막 원문과 번역문을 감싸는 패널을 생성한다.
- `self.`를 사용했으므로 다른 메서드에서도 패널에 접근할 수 있다.

```python
self.panel.setObjectName("subtitlePanel")
```

- 패널에 `subtitlePanel`이라는 이름을 지정한다.
- 아래 스타일시트에서 해당 이름을 기준으로 디자인을 적용한다.

```python
panel_layout = QVBoxLayout(self.panel)
```

- 자막 패널 내부에 세로 레이아웃을 생성한다.
- 원문과 번역문을 위아래로 배치하기 위한 레이아웃이다.

```python
panel_layout.setContentsMargins(28, 18, 28, 18)
```

- 패널 내부 여백을 설정한다.
- 왼쪽 28, 위쪽 18, 오른쪽 28, 아래쪽 18이다.

```python
panel_layout.setSpacing(7)
```

- 원문 라벨과 번역문 라벨 사이의 간격을 7로 설정한다.

```python
self.original_label = QLabel("강의 원문이 여기에 표시됩니다.")
```

- 강의에서 인식한 원문을 표시할 라벨을 만든다.
- 초기 화면에는 안내 문구가 표시된다.

```python
self.original_label.setObjectName("originalText")
```

- 원문 라벨에 `originalText`라는 이름을 지정한다.

```python
self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
```

- 원문 텍스트를 가운데 정렬한다.

```python
self.original_label.setWordWrap(True)
```

- 원문이 길어지면 자동으로 줄바꿈하도록 설정한다.

```python
self.translated_label = QLabel("Translated subtitles will appear here.")
```

- 번역 결과를 표시할 라벨을 생성한다.
- 초기에는 영어 안내 문구가 표시된다.

```python
self.translated_label.setObjectName("translatedText")
```

- 번역문 라벨에 `translatedText`라는 이름을 지정한다.

```python
self.translated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
```

- 번역문을 가운데 정렬한다.

```python
self.translated_label.setWordWrap(True)
```

- 번역문이 길어지면 자동 줄바꿈하도록 설정한다.

```python
panel_layout.addWidget(self.original_label)
```

- 패널 내부 레이아웃에 원문 라벨을 추가한다.

```python
panel_layout.addWidget(self.translated_label)
```

- 패널 내부 레이아웃에 번역문 라벨을 추가한다.
- 결과적으로 원문이 위쪽, 번역문이 아래쪽에 표시된다.

```python
root.addWidget(self.panel, alignment=Qt.AlignmentFlag.AlignHCenter)
```

- 자막 패널을 오버레이의 최상위 레이아웃에 추가한다.
- `AlignHCenter`는 패널을 가로 방향 가운데에 정렬한다.

---

## 10. 오버레이 스타일시트

```python
self.setStyleSheet("""
```

- 오버레이 창에 Qt 스타일시트(QSS)를 적용하기 시작한다.

```css
QFrame#subtitlePanel {
```

- 이름이 `subtitlePanel`인 QFrame에 적용할 스타일을 시작한다.

```css
background-color: rgba(12, 18, 30, 205);
```

- 패널 배경을 어두운 남색으로 설정한다.
- `rgba()`는 빨강, 초록, 파랑, 알파 값을 지정한다.
- 마지막 `205`는 불투명도에 해당하는 알파 값으로, 최대 255보다 작기 때문에 반투명하다.

```css
border: 1px solid rgba(255, 255, 255, 55);
```

- 흰색 계열의 반투명 테두리를 1픽셀로 적용한다.

```css
border-radius: 14px;
```

- 패널 모서리를 14픽셀 둥글게 만든다.

```css
}
```

- 자막 패널 스타일을 끝낸다.

```css
QLabel#originalText {
```

- 원문 라벨의 스타일을 시작한다.

```css
color: rgba(255, 255, 255, 220);
```

- 원문을 거의 불투명한 흰색으로 표시한다.

```css
font-size: 17pt;
```

- 원문 글자 크기를 17pt로 설정한다.

```css
font-weight: 600;
```

- 원문 글자를 약간 굵게 표시한다.

```css
}
```

- 원문 라벨 스타일을 끝낸다.

```css
QLabel#translatedText {
```

- 번역문 라벨의 스타일을 시작한다.

```css
color: #93c5fd;
```

- 번역문을 연한 파란색으로 표시한다.

```css
font-size: 19pt;
```

- 번역문 글자 크기를 19pt로 설정한다.
- 원문보다 크게 표시한다.

```css
font-weight: 700;
```

- 번역문을 굵게 표시한다.

```css
}
```

- 번역문 라벨 스타일을 끝낸다.

```python
""")
```

- 스타일시트 문자열을 끝내고 오버레이 창에 적용한다.

```python
self.setMinimumWidth(700)
```

- 오버레이 창의 최소 너비를 700픽셀로 설정한다.
- 창 너비가 이 값보다 작아지지 않도록 제한한다.

---

## 11. 시스템 트레이 아이콘: \_create_tray_icon()

```python
def _create_tray_icon(self):
```

- Windows 작업 표시줄 알림 영역에 표시할 아이콘과 메뉴를 만드는 메서드다.

```python
# The tray menu remains available while the overlay is click-through.
```

- 오버레이가 클릭 통과 상태여도 트레이 메뉴를 통해 제어할 수 있다는 설명이다.

```python
self.tray = QSystemTrayIcon(self)
```

- 시스템 트레이 아이콘 객체를 생성한다.
- `self`를 부모 객체로 전달한다.
- Qt 객체의 부모-자식 관계를 통해 생명주기를 관리할 수 있다.

```python
self.tray.setToolTip("Live Translator Overlay")
```

- 트레이 아이콘 위에 마우스를 올렸을 때 표시할 설명을 지정한다.

```python
self.tray.setIcon(
    self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
)
```

- 시스템 트레이에 표시할 아이콘을 지정한다.
- `self.style()`은 현재 위젯의 스타일 객체를 가져온다.
- `standardIcon()`은 Qt에서 제공하는 기본 아이콘을 가져온다.
- `SP_ComputerIcon`은 컴퓨터 모양의 기본 아이콘이다.

```python
menu = QMenu()
```

- 트레이 아이콘을 우클릭했을 때 표시할 메뉴를 생성한다.

```python
exit_action = menu.addAction("오버레이 종료")
```

- 메뉴에 `오버레이 종료` 항목을 추가한다.
- 반환된 액션 객체를 `exit_action`에 저장한다.

```python
exit_action.triggered.connect(QApplication.quit)
```

- 메뉴 항목을 선택하면 애플리케이션 종료 함수를 호출하도록 연결한다.
- `triggered`는 메뉴 항목이 실행되었을 때 발생하는 시그널이다.
- 주의할 점: 이 코드는 오버레이만 숨기는 것이 아니라 **현재 Qt 애플리케이션 전체를 종료**한다.

```python
self.tray.setContextMenu(menu)
```

- 생성한 메뉴를 트레이 아이콘의 우클릭 메뉴로 지정한다.

```python
self.tray.show()
```

- 시스템 트레이 아이콘을 화면에 표시한다.

---

## 12. 자막 변경 기능: set_subtitle()

```python
def set_subtitle(self, original_text: str, translated_text: str):
```

- 오버레이에 표시되는 원문과 번역문을 변경하는 메서드다.
- `original_text`: 원문 문자열을 전달받는다.
- `translated_text`: 번역된 문자열을 전달받는다.
- 두 인자는 문자열이라는 타입 힌트가 붙어 있다.

```python
"""Update subtitles. Call on the GUI thread via Qt Signal/Slot."""
```

- 자막을 갱신하는 메서드라는 설명이다.
- GUI 위젯을 변경하는 작업은 Qt GUI 스레드에서 수행해야 한다는 주의사항도 포함한다.

```python
self.original_label.setText(original_text)
```

- 원문 라벨의 내용을 전달받은 원문으로 변경한다.

```python
self.translated_label.setText(translated_text)
```

- 번역문 라벨의 내용을 전달받은 번역문으로 변경한다.

```python
self.panel.adjustSize()
```

- 패널 내부 내용에 맞게 패널 크기를 다시 계산하도록 요청한다.
- 문장 길이가 바뀌었을 때 패널 크기가 적절히 조정되도록 하는 목적이다.

이 메서드는 향후 STT와 번역 모듈을 연결할 때 중요한 인터페이스가 된다.

예를 들어 번역 모듈에서 결과가 나오면 다음처럼 호출할 수 있다.

```python
overlay.set_subtitle(
    "오늘은 인공지능을 공부합니다.",
    "Today, we are studying artificial intelligence."
)
```

실제 프로젝트에서는 작업 스레드에서 직접 UI를 변경하지 않고 Qt Signal/Slot을 통해 GUI 스레드로 전달해야 한다.

---

## 13. 자막 초기화: clear_subtitle()

```python
def clear_subtitle(self):
```

- 현재 표시 중인 원문과 번역문을 비우는 메서드다.

```python
self.original_label.clear()
```

- 원문 라벨의 텍스트를 제거한다.

```python
self.translated_label.clear()
```

- 번역문 라벨의 텍스트를 제거한다.

---

## 14. 창 표시 이벤트: showEvent()

```python
def showEvent(self, event):
```

- Qt에서 창이 표시될 때 호출되는 이벤트 메서드다.
- 오버레이가 화면에 나타나는 시점에 필요한 후속 처리를 수행한다.

```python
super().showEvent(event)
```

- 부모 클래스인 `QWidget`의 기본 `showEvent()` 처리를 실행한다.
- 기본 이벤트 처리를 유지하기 위해 호출한다.

```python
# Native HWND is available after the widget is shown.
```

- 위젯이 화면에 표시된 뒤 Windows 네이티브 창 핸들을 사용할 수 있다는 설명이다.

```python
QTimer.singleShot(0, self._apply_native_styles)
```

- 0밀리초 뒤에 `_apply_native_styles()`를 한 번 실행하도록 예약한다.
- 즉시 실행하는 것처럼 보이지만 현재 이벤트 처리가 끝난 뒤 실행될 수 있도록 Qt 이벤트 큐에 작업을 등록한다.
- 이 시점에 창 핸들을 가져와 Windows 스타일을 적용한다.

---

## 15. Windows 스타일 적용: \_apply_native_styles()

```python
def _apply_native_styles(self):
```

- 현재 오버레이 창에 Windows 네이티브 스타일을 적용하는 메서드다.

```python
if sys.platform != "win32":
```

- 현재 실행 중인 운영체제가 Windows가 아닌지 확인한다.
- `win32`가 아니라면 Windows 전용 API를 실행하지 않는다.

```python
print("[OVERLAY] Click-through는 Windows에서만 지원됩니다.", flush=True)
```

- Windows가 아닌 환경에서는 클릭 통과 기능을 지원하지 않는다는 메시지를 출력한다.

```python
return
```

- 함수 실행을 종료한다.
- 따라서 Windows API 호출 부분으로 내려가지 않는다.

```python
hwnd = int(self.winId())
```

- Qt 위젯의 네이티브 창 핸들을 가져온다.
- `winId()`는 Qt 위젯에 대응하는 네이티브 창 식별자를 반환한다.
- `int()`를 사용해 정수로 변환한다.

```python
enable_click_through(hwnd)
```

- 앞에서 정의한 Windows API 함수에 창 핸들을 전달한다.
- 해당 창에 클릭 통과와 최상단 표시 등의 확장 스타일을 적용한다.

```python
print("[OVERLAY] WS_EX_TRANSPARENT 적용 완료", flush=True)
```

- Windows 확장 스타일 적용이 끝났다는 로그를 출력한다.

---

## 16. 전체 화면 오버레이 표시

```python
def show_fullscreen_overlay(self):
```

- 오버레이 창을 화면 전체 크기로 표시하는 메서드다.
- `poc_config.py`의 강의 시작 버튼에서도 호출한다.

```python
screen = QApplication.primaryScreen()
```

- 현재 애플리케이션의 기본 화면 정보를 가져온다.
- 멀티 모니터 환경에서는 기본 화면을 기준으로 한다.

```python
if screen is None:
```

- 사용 가능한 화면 정보가 없는지 확인한다.

```python
raise RuntimeError("사용 가능한 디스플레이를 찾을 수 없습니다.")
```

- 화면을 찾지 못했다면 예외를 발생시킨다.
- 화면 정보 없이 오버레이 위치와 크기를 설정할 수 없기 때문이다.

```python
self.setGeometry(screen.geometry())
```

- 오버레이 창의 위치와 크기를 화면의 전체 영역에 맞춘다.
- `screen.geometry()`는 해당 화면의 위치와 크기를 반환한다.
- `setGeometry()`는 창의 위치와 크기를 한 번에 설정한다.

```python
self.show()
```

- 오버레이 창을 표시한다.
- 이때 `showEvent()`도 호출되므로 네이티브 스타일 적용 작업이 예약된다.

```python
self.raise_()
```

- 창을 표시 순서상 위로 올리도록 요청한다.
- 다른 창 위에 표시하기 위한 보조 처리다.
- Windows의 `HWND_TOPMOST` 설정도 별도로 적용된다.

---

## 17. 전역 종료 단축키 등록

```python
def register_exit_hotkey(self):
```

- Ctrl + Shift + Q 전역 단축키를 등록하는 메서드다.

```python
if sys.platform != "win32" or self._hotkey_registered:
```

- Windows가 아닌 환경이거나 이미 단축키가 등록된 상태인지 확인한다.
- 둘 중 하나라도 참이면 등록을 진행하지 않는다.

```python
return
```

- 단축키 등록을 중단하고 메서드에서 빠져나간다.

```python
user32 = ctypes.windll.user32
```

- Windows GUI API인 `user32.dll`에 접근한다.

```python
self._hotkey_registered = bool(
    user32.RegisterHotKey(
        None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_Q
    )
)
```

- Windows에 전역 단축키를 등록한다.
- `None`: 특정 창에 연결하지 않고 현재 호출 스레드에 단축키 메시지를 전달하도록 한다.
- `HOTKEY_ID`: 등록할 단축키의 식별 번호다.
- `MOD_CONTROL | MOD_SHIFT`: Ctrl과 Shift 조합을 지정한다.
- `VK_Q`: Q 키를 지정한다.
- `RegisterHotKey()`의 성공 여부를 `bool()`로 변환해 저장한다.
- 성공하면 `True`, 실패하면 `False`가 된다.

```python
if not self._hotkey_registered:
```

- 단축키 등록에 실패했는지 확인한다.

```python
print("[OVERLAY] 전역 단축키 등록 실패. 시스템 트레이 메뉴로 종료하세요.", flush=True)
```

- 등록 실패 메시지를 출력한다.
- 트레이 메뉴를 이용해 종료할 수 있다고 안내한다.

```python
else:
```

- 단축키 등록에 성공한 경우 실행된다.

```python
print("[OVERLAY] 종료 단축키: Ctrl + Shift + Q", flush=True)
```

- 등록된 종료 단축키를 콘솔에 출력한다.

---

## 18. 전역 종료 단축키 해제

```python
def unregister_exit_hotkey(self):
```

- 등록했던 전역 단축키를 해제하는 메서드다.

```python
if sys.platform == "win32" and self._hotkey_registered:
```

- Windows 환경이고 단축키가 실제로 등록된 상태인지 확인한다.

```python
ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
```

- Windows API를 호출해 등록된 단축키를 해제한다.
- 등록할 때 사용한 식별 번호인 `HOTKEY_ID`를 전달한다.

```python
self._hotkey_registered = False
```

- 단축키가 해제되었음을 객체 내부 상태에 반영한다.
- 이후 중복 해제나 등록 상태 혼동을 방지한다.

---

## 19. 단축키 메시지 확인: \_check_hotkey()

```python
def _check_hotkey():
```

- Windows 메시지 큐에 전역 단축키 메시지가 들어왔는지 확인하는 함수다.
- 클래스 내부가 아니라 모듈 최상위에 정의되어 있다.

```python
if sys.platform != "win32":
```

- Windows가 아닌 환경인지 확인한다.

```python
return
```

- Windows가 아니라면 함수를 종료한다.

```python
msg = ctypes.wintypes.MSG()
```

- Windows 메시지를 저장할 `MSG` 구조체 객체를 만든다.
- Windows 메시지에는 메시지 종류, 대상 창, 추가 정보 등이 포함된다.

```python
user32 = ctypes.windll.user32
```

- `user32.dll`에 접근한다.

```python
while user32.PeekMessageW(
    ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1
):
```

- 메시지 큐에서 `WM_HOTKEY` 메시지가 있는지 확인한다.
- `PeekMessageW()`는 메시지가 도착할 때까지 기다리는 함수가 아니라 메시지 큐를 확인하는 함수다.
- `ctypes.byref(msg)`: 메시지 정보를 기록할 구조체의 주소를 전달한다.
- `None`: 특정 창에 한정하지 않고 현재 스레드의 메시지 큐를 확인한다.
- `WM_HOTKEY`: 확인할 메시지의 최소 범위다.
- 두 번째 `WM_HOTKEY`: 확인할 메시지의 최대 범위다.
- 마지막 `1`: 확인한 메시지를 큐에서 제거하는 `PM_REMOVE` 값이다.
- 해당 메시지가 있으면 반복문을 실행한다.

```python
if msg.wParam == HOTKEY_ID:
```

- 메시지에 기록된 단축키 식별 번호가 우리가 등록한 `HOTKEY_ID`인지 확인한다.

```python
QApplication.quit()
```

- 등록한 단축키가 눌렸다면 Qt 애플리케이션 종료를 요청한다.
- 종료 요청 후 이벤트 루프가 종료되면 프로그램이 끝난다.

---

## 20. 독립 실행 함수: main()

```python
def main():
```

- 이 파일을 단독으로 실행할 때 필요한 시작 절차를 정의한다.

```python
app = QApplication(sys.argv)
```

- Qt 애플리케이션 객체를 생성한다.
- 이벤트 루프와 UI 이벤트 처리를 관리한다.

```python
app.setApplicationName("Live Translator Overlay")
```

- 애플리케이션 이름을 지정한다.

```python
overlay = SubtitleOverlay()
```

- 자막 오버레이 객체를 생성한다.
- 이때 `SubtitleOverlay.__init__()`이 실행된다.
- UI 구성과 트레이 아이콘 생성도 이 과정에서 진행된다.

```python
overlay.show_fullscreen_overlay()
```

- 오버레이를 기본 모니터 전체 크기로 표시한다.

```python
overlay.register_exit_hotkey()
```

- Ctrl + Shift + Q 전역 단축키를 등록한다.

```python
overlay.set_subtitle(
    "안녕하세요. 오늘은 인공지능의 기본 개념을 살펴보겠습니다.",
    "Hello. Today, we will explore the basic concepts of artificial intelligence.",
)
```

- 테스트용 원문과 번역문을 오버레이에 표시한다.
- 실제 STT나 번역 결과가 아니라 하드코딩된 테스트 문자열이다.
- 실제 프로젝트에서는 이 위치에 번역 파이프라인의 결과를 전달하게 된다.

```python
hotkey_timer = QTimer()
```

- 단축키 메시지를 주기적으로 확인할 타이머 객체를 생성한다.

```python
hotkey_timer.timeout.connect(_check_hotkey)
```

- 타이머가 timeout 이벤트를 발생시키면 `_check_hotkey()`를 실행하도록 연결한다.

```python
hotkey_timer.start(100)
```

- 타이머를 시작한다.
- 100밀리초마다 timeout 이벤트가 발생한다.
- 결과적으로 약 0.1초 간격으로 Windows 메시지 큐를 확인한다.

```python
app.aboutToQuit.connect(overlay.unregister_exit_hotkey)
```

- 애플리케이션 종료 직전에 전역 단축키를 해제하도록 연결한다.
- 정상적인 종료 과정에서 단축키가 계속 등록된 채 남는 상황을 방지한다.

```python
sys.exit(app.exec())
```

- Qt 이벤트 루프를 실행한다.
- 창 표시, 타이머, 메뉴 선택, 단축키 처리 등의 이벤트가 이 루프에서 처리된다.
- 이벤트 루프가 끝나면 프로그램을 종료한다.

---

## 21. 직접 실행 여부 확인

```python
if __name__ == "__main__":
```

- 현재 파일을 직접 실행했는지 확인한다.
- 다른 파일에서 `import poc_overlay`로 가져오면 이 조건은 거짓이다.

```python
main()
```

- 파일을 직접 실행한 경우 `main()`을 호출한다.
- 따라서 `python poc_overlay.py`로 실행하면 오버레이 단독 테스트가 시작된다.

---

# 22. 실제 프로젝트에서 중요한 연결 관계와 주의사항

## A. 설정 창에서 오버레이를 호출하는 경우

`poc_config.py`에서는 다음과 같이 오버레이를 생성한다.

```python
self.overlay = SubtitleOverlay()
```

강의 시작 버튼을 누르면 다음 메서드가 실행된다.

```python
self.overlay.show_fullscreen_overlay()
```

강의 종료 버튼을 누르면 다음 메서드가 실행된다.

```python
self.overlay.hide()
```

즉, 설정 창이 오버레이 객체를 소유하고 표시 여부를 제어하는 구조다.

## B. 현재 코드에서 단축키 관련 주의점

현재 `poc_config.py`의 실행 흐름에서는 다음 두 작업이 빠져 있다.

```python
self.overlay.register_exit_hotkey()
```

```python
hotkey_timer.timeout.connect(_check_hotkey)
```

두 작업은 현재 `poc_overlay.py`의 독립 실행용 `main()` 안에서만 수행된다.

따라서 `poc_config.py`를 실행한 경우에는 Ctrl + Shift + Q가 자동으로 동작하지 않는다. 단축키를 설정 창에서도 사용하려면 등록뿐 아니라 메시지를 확인하는 타이머도 설정 창 실행 흐름에 연결해야 한다.

## C. GUI 스레드 주의사항

`set_subtitle()`은 QLabel의 텍스트를 직접 변경한다.

Qt에서는 GUI 위젯을 작업 스레드에서 직접 변경하면 문제가 생길 수 있다. 실제 STT와 번역 작업은 별도 스레드에서 실행하고, 결과를 Qt Signal/Slot으로 GUI 스레드에 전달하는 구조가 적절하다.

## D. 트레이 메뉴 종료 동작

현재 코드는 다음과 같이 연결되어 있다.

```python
exit_action.triggered.connect(QApplication.quit)
```

이 동작은 오버레이만 숨기는 것이 아니라 애플리케이션 전체를 종료한다.

설정 창까지 함께 실행하는 구조에서는 트레이 메뉴를 눌렀을 때 전체 프로그램이 종료된다는 점을 알고 있어야 한다.

---

# 23. 전체 동작 흐름 요약

```text
poc_config.py
    │
    ├── ConfigWindow 생성
    │
    └── SubtitleOverlay 생성
             │
             ├── 오버레이 UI 생성
             ├── 원문 QLabel 생성
             ├── 번역문 QLabel 생성
             └── 트레이 아이콘 생성

사용자가 강의 시작
    │
    └── show_fullscreen_overlay()
             │
             ├── 기본 모니터 정보 가져오기
             ├── 화면 크기로 창 크기 설정
             ├── 오버레이 표시
             └── Windows 확장 스타일 적용

번역 결과 도착
    │
    └── set_subtitle(original, translated)
             │
             ├── 원문 라벨 갱신
             ├── 번역문 라벨 갱신
             └── 패널 크기 조정

사용자가 강의 종료
    │
    └── overlay.hide()
```

**핵심 정리:** `poc_overlay.py`는 단순히 텍스트를 띄우는 창이 아니라, Qt로 UI를 만들고 Windows API로 창의 동작 방식을 조정하는 모듈이다. 실제 번역 기능을 연결할 때 가장 중요한 메서드는 `set_subtitle()`이다.
