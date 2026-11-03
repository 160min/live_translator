import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QVBoxLayout, QWidget, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QScrollArea 예제")
        self.resize(300, 400)

        # 1. QScrollArea 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # 내부 위젯 크기 자동 조절 활성화

        # 2. 스크롤 영역 내부에 들어갈 '실제 위젯'과 레이아웃 생성
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # 예시를 위해 버튼 30개 추가 (화면 세로 크기를 넘어가도록)
        for i in range(1, 31):
            layout.addWidget(QPushButton(f"버튼 {i}"))

        # 3. 스크롤 영역에 콘텐츠 위젯을 세팅
        scroll_area.setWidget(content_widget)

        # 4. QScrollArea를 메인 창의 중심 위젯으로 설정
        self.setCentralWidget(scroll_area)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
