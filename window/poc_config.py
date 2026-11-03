import sys
from pathlib import Path

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
)

from poc_overlay import SubtitleOverlay


class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_file: str | None = None

        # The overlay is owned by the config window and controlled by its buttons.
        self.overlay = SubtitleOverlay()

        self.setWindowTitle("Live Translator | Control Panel")
        # Allow compact windows; the content scrolls vertically when needed.
        self.setMinimumSize(340, 260)
        self.resize(540, 430)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        # A scroll area prevents controls from being clipped when the window
        # is resized smaller than the preferred content height.
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        central = QWidget()
        central.setObjectName("contentWidget")
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Live Translator")
        title.setObjectName("title")

        subtitle = QLabel("강의 실시간 번역 오버레이")
        subtitle.setObjectName("subtitle")

        header = QVBoxLayout()
        header.setSpacing(4)
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        file_card = QFrame()
        file_card.setObjectName("card")
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(18, 16, 18, 16)
        file_layout.setSpacing(10)

        file_heading = QLabel("강의 자료 (선택 사항)")
        file_heading.setObjectName("sectionTitle")

        self.file_label = QLabel("첨부된 파일이 없습니다. 파일 없이도 강의를 시작할 수 있습니다.")
        self.file_label.setObjectName("fileLabel")
        self.file_label.setWordWrap(True)

        self.attach_button = QPushButton("＋  PPT 첨부하기")
        self.attach_button.setObjectName("attachButton")
        self.attach_button.setMinimumHeight(44)
        self.attach_button.setToolTip("강의 자료는 첨부하지 않아도 강의를 시작할 수 있습니다.")
        self.attach_button.clicked.connect(self.on_attach_clicked)

        file_layout.addWidget(file_heading)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.attach_button)
        root.addWidget(file_card)

        action_heading = QLabel("강의 제어")
        action_heading.setObjectName("sectionTitle")
        root.addWidget(action_heading)

        self.start_button = QPushButton("강의 시작")
        self.start_button.setObjectName("startButton")
        self.start_button.setMinimumHeight(48)
        self.start_button.clicked.connect(self.on_start_clicked)

        self.stop_button = QPushButton("강의 종료")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setMinimumHeight(48)
        self.stop_button.clicked.connect(self.on_stop_clicked)

        root.addWidget(self.start_button)
        root.addWidget(self.stop_button)

        self.status_label = QLabel("상태: 대기 중")
        self.status_label.setObjectName("status")
        root.addWidget(self.status_label)

        note = QLabel("Week 1 PoC · PPT 첨부는 선택 사항입니다")
        note.setObjectName("footer")
        root.addWidget(note)

        scroll.setWidget(central)
        self.setCentralWidget(scroll)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #111827;
                color: #F9FAFB;
                font-family: "Malgun Gothic", "맑은 고딕", sans-serif;
                font-size: 10pt;
            }
            QScrollArea#mainScroll {
                border: none;
                background-color: #111827;
            }
            QLabel#title {
                font-size: 21pt;
                font-weight: 700;
                color: #F9FAFB;
            }
            QLabel#subtitle {
                color: #9CA3AF;
                font-size: 10pt;
            }
            QFrame#card {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 12px;
            }
            QLabel#sectionTitle {
                color: #E5E7EB;
                font-size: 11pt;
                font-weight: 700;
            }
            QLabel#fileLabel {
                color: #D1D5DB;
                padding: 5px 0;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 9px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                border: 1px solid #93C5FD;
            }
            QPushButton#attachButton {
                background-color: #374151;
                color: #F9FAFB;
                text-align: left;
                border: 1px solid #4B5563;
            }
            QPushButton#attachButton:hover {
                background-color: #4B5563;
                border: 1px solid #60A5FA;
            }
            QPushButton#startButton {
                background-color: #2563EB;
                color: white;
                font-size: 11pt;
            }
            QPushButton#startButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton#stopButton {
                background-color: #374151;
                color: #FCA5A5;
                font-size: 11pt;
            }
            QPushButton#stopButton:hover {
                background-color: #4B5563;
            }
            QLabel#status {
                color: #93C5FD;
                padding-top: 4px;
            }
            QLabel#footer {
                color: #6B7280;
                font-size: 8pt;
                padding-top: 4px;
            }
        """)

    def on_attach_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "PPT / PDF 강의 자료 선택",
            "",
            "강의 자료 (*.pptx *.ppt *.pdf);;PowerPoint (*.pptx *.ppt);;PDF (*.pdf)",
        )
        if not file_path:
            return

        self.selected_file = file_path
        self.file_label.setText(f"첨부됨: {Path(file_path).name}")
        print(f"[CONFIG] 파일 첨부: {file_path}", flush=True)

    def on_start_clicked(self):
        print("시작 버튼 눌림", flush=True)

        if self.selected_file:
            print(f"[CONFIG] 선택된 강의 자료: {self.selected_file}", flush=True)
        else:
            print("[CONFIG] 강의 자료 없이 시작합니다.", flush=True)

        # Show the click-through overlay when the lecture starts.
        self.overlay.show_fullscreen_overlay()
        self.status_label.setText("상태: 강의 진행 중")
        print("[CONFIG] 자막 오버레이 표시", flush=True)

    def on_stop_clicked(self):
        print("종료 버튼 눌림", flush=True)

        # Hide the overlay but keep the config window running.
        self.overlay.hide()
        self.status_label.setText("상태: 대기 중")
        print("[CONFIG] 자막 오버레이 숨김", flush=True)

    def closeEvent(self, event):
        # Ensure the overlay is also closed when the control panel exits.
        self.overlay.close()
        if hasattr(self.overlay, "unregister_exit_hotkey"):
            self.overlay.unregister_exit_hotkey()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Live Translator")

    window = ConfigWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
