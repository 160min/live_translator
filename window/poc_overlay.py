"""
Live Translator - Week 1 PoC
Transparent, always-on-top, click-through subtitle overlay.

This module can be run standalone for overlay testing, or imported by
poc_config.py so the config window can show/hide the overlay.
"""

import ctypes
import ctypes.wintypes
import sys

from PySide6.QtCore import Qt, QTimer
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

# Windows extended window styles
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

# Windows positioning constants
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

# Global hotkey: Ctrl + Shift + Q
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
WM_HOTKEY = 0x0312
HOTKEY_ID = 1
VK_Q = 0x51


def enable_click_through(hwnd: int):
    """Apply native Windows styles so mouse input passes through this window."""
    user32 = ctypes.windll.user32

    get_style = user32.GetWindowLongPtrW
    set_style = user32.SetWindowLongPtrW
    get_style.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
    get_style.restype = ctypes.c_ssize_t
    set_style.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    set_style.restype = ctypes.c_ssize_t

    ex_style = get_style(hwnd, GWL_EXSTYLE)
    ex_style |= (
        WS_EX_LAYERED
        | WS_EX_TRANSPARENT
        | WS_EX_TOOLWINDOW
        | WS_EX_NOACTIVATE
    )
    set_style(hwnd, GWL_EXSTYLE, ex_style)

    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
    )


class SubtitleOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Live Translator Overlay")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._hotkey_registered = False
        self._build_ui()
        self._create_tray_icon()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(80, 0, 80, 55)
        root.addStretch(1)

        self.panel = QFrame()
        self.panel.setObjectName("subtitlePanel")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 18, 28, 18)
        panel_layout.setSpacing(7)

        self.original_label = QLabel("강의 원문이 여기에 표시됩니다.")
        self.original_label.setObjectName("originalText")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setWordWrap(True)

        self.translated_label = QLabel("Translated subtitles will appear here.")
        self.translated_label.setObjectName("translatedText")
        self.translated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translated_label.setWordWrap(True)

        panel_layout.addWidget(self.original_label)
        panel_layout.addWidget(self.translated_label)
        root.addWidget(self.panel, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setStyleSheet("""
            QFrame#subtitlePanel {
                background-color: rgba(12, 18, 30, 205);
                border: 1px solid rgba(255, 255, 255, 55);
                border-radius: 14px;
            }
            QLabel#originalText {
                color: rgba(255, 255, 255, 220);
                font-size: 17pt;
                font-weight: 600;
            }
            QLabel#translatedText {
                color: #93C5FD;
                font-size: 19pt;
                font-weight: 700;
            }
        """)
        self.setMinimumWidth(700)

    def _create_tray_icon(self):
        # The tray menu remains available while the overlay is click-through.
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Live Translator Overlay")
        self.tray.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        )

        menu = QMenu()
        exit_action = menu.addAction("오버레이 종료")
        exit_action.triggered.connect(QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def set_subtitle(self, original_text: str, translated_text: str):
        """Update subtitles. Call on the GUI thread via Qt Signal/Slot."""
        self.original_label.setText(original_text)
        self.translated_label.setText(translated_text)
        self.panel.adjustSize()

    def clear_subtitle(self):
        self.original_label.clear()
        self.translated_label.clear()

    def showEvent(self, event):
        super().showEvent(event)
        # Native HWND is available after the widget is shown.
        QTimer.singleShot(0, self._apply_native_styles)

    def _apply_native_styles(self):
        if sys.platform != "win32":
            print("[OVERLAY] Click-through는 Windows에서만 지원됩니다.", flush=True)
            return

        hwnd = int(self.winId())
        enable_click_through(hwnd)
        print("[OVERLAY] WS_EX_TRANSPARENT 적용 완료", flush=True)

    def show_fullscreen_overlay(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("사용 가능한 디스플레이를 찾을 수 없습니다.")

        self.setGeometry(screen.geometry())
        self.show()
        self.raise_()

    def register_exit_hotkey(self):
        if sys.platform != "win32" or self._hotkey_registered:
            return

        user32 = ctypes.windll.user32
        self._hotkey_registered = bool(
            user32.RegisterHotKey(
                None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_Q
            )
        )
        if not self._hotkey_registered:
            print("[OVERLAY] 전역 단축키 등록 실패. 시스템 트레이 메뉴로 종료하세요.", flush=True)
        else:
            print("[OVERLAY] 종료 단축키: Ctrl + Shift + Q", flush=True)

    def unregister_exit_hotkey(self):
        if sys.platform == "win32" and self._hotkey_registered:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
            self._hotkey_registered = False


def _check_hotkey():
    if sys.platform != "win32":
        return

    msg = ctypes.wintypes.MSG()
    user32 = ctypes.windll.user32
    while user32.PeekMessageW(
        ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1
    ):
        if msg.wParam == HOTKEY_ID:
            QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Live Translator Overlay")

    overlay = SubtitleOverlay()
    overlay.show_fullscreen_overlay()
    overlay.register_exit_hotkey()
    overlay.set_subtitle(
        "안녕하세요. 오늘은 인공지능의 기본 개념을 살펴보겠습니다.",
        "Hello. Today, we will explore the basic concepts of artificial intelligence.",
    )

    hotkey_timer = QTimer()
    hotkey_timer.timeout.connect(_check_hotkey)
    hotkey_timer.start(100)

    app.aboutToQuit.connect(overlay.unregister_exit_hotkey)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
