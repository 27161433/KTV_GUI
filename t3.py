from PySide6.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QRect, QSize, QPropertyAnimation, QEasingCurve

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QFrame(self)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.frame = QFrame(self.central_widget)
        self.frame.setStyleSheet("background-color: blue; border-radius: 25px;")
        self.central_layout.addWidget(self.frame)

        self.button = QPushButton("放大", self.central_widget)
        self.central_layout.addWidget(self.button)

        self.button.clicked.connect(self.animate_frame)

    def animate_frame(self):
        window_size = self.central_widget.size()
        target_size = QSize(window_size.width(), window_size.height())

        animation = QPropertyAnimation(self.frame, b"geometry", self)
        animation.setDuration(1000)
        animation.setStartValue(QRect(0, 0, 50, 50))  # 初始尺寸
        animation.setEndValue(QRect(0, 0, target_size.width(), target_size.height()))
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        animation.start()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
