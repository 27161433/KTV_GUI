from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QScrollArea, QLineEdit, QMenu, QGraphicsDropShadowEffect, QTextEdit, QFrame, QProgressBar
from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase, QMovie, QResizeEvent, QMouseEvent, QKeyEvent, QAction, QCursor, QColor, QIcon, QWheelEvent, QPainter, QBrush, QPainterPath, QEnterEvent, QPen
from PySide6.QtCore import Qt, QRegularExpression, QUrl, QEasingCurve, QThread, Signal, QTimer, QPropertyAnimation, QPoint, Property, QPointF, QRect, QParallelAnimationGroup, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudio, QMediaFormat
from PySide6.QtMultimediaWidgets import QVideoWidget
from qframelesswindow import FramelessWindow, AcrylicWindow
from subprocess import Popen, PIPE, STDOUT
import yt_dlp as ytdl
import sys

class LoadingIMG(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QPixmap("./img/loading_icon.png")
        self.setPixmap(self.image.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.setPixmap(self.image.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio))

class Loading(QWidget):
    aniF = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()

        self.c = False
        self.image_label = LoadingIMG(self)
        self.animation = QPropertyAnimation(self.image_label, b"geometry")
        self.animation.setDuration(750)
        self._size = min(self.width(), self.height())

        self.ss = IconAni("./img/loading_icon.png", self)
        self.ss.setGeometry(100, 100, 40, 40)

    def startAni(self):
        self._size = min(self.width(), self.height())
        self.c = False
        self.show()
        self.animation.finished.connect(self.ani2)
        self.ani1()
        
    def ani1(self):
        self._size = min(self.width(), self.height())
        self.l_size = max(self.height(), self.width())
        p = -round(self.l_size / 2)
        s = self.l_size * 2
        _s = self._size / 10 * 2
        self.animation.setStartValue(QRect(p, p, s, s))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.start()
        self.animation.finished.disconnect()
        self.animation.finished.connect(self.ani2)

    def ani2(self):
        self._size = min(self.width(), self.height())
        s = self._size / 10 * 2
        _s = self._size / 10 * 4

        self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.start()
        self.animation.finished.disconnect()
        self.animation.finished.connect(self.ani3)

    def ani3(self):
        self._size = min(self.width(), self.height())
        s = self._size / 10 * 4
        _s = self._size / 10 * 2

        self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.finished.disconnect()
        self.animation.start()
        if not self.c:
            self.animation.finished.connect(self.ani2)
        else:
            self.animation.finished.connect(self.ani4)

    def ani4(self):
        self._size = min(self.width(), self.height())
        self.l_size = max(self.height(), self.width())
        s = self._size / 10 * 2
        p = -self.l_size
        _s = self.l_size * 3

        self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(p, p, _s, _s))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.start()
        self.animation.finished.disconnect()
        self.animation.finished.connect(self.animationFinish)

    def animationFinish(self):
        self.hide()
        self.aniF.emit()

class IconAni(QLabel):
    def __init__(self, img, parent=None):
        super().__init__(parent)

        self.l = 60

        self.c = False

        self.w = self.width()
        self.h = self.height()
        self._x = self.x()
        self._y = self.y()

        self.pix = QPixmap(img)

        self.setPixmap(self.pix.scaled(self.w, self.h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setStyleSheet("background: black; border-radius: 20px;")

        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(1)
        self.setGraphicsEffect(self.opacity_effect)

        self.ani = QPropertyAnimation(self, b"geometry")
        self.ani.setDuration(750)
        self.ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ani2 = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.ani2.setDuration(750)
        self.ani2.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.setGroup = QParallelAnimationGroup(self)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.setPixmap(self.pix.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setStyleSheet(f"background: black; border-radius: {self.width() // 2}px;")

    def aniStart(self):
        self.ani.setStartValue(QRect(self._x, self._y, self.w, self.h))
        self.ani.setEndValue(QRect(self._x - round((self.l - self.w) / 2), self._y - round((self.l - self.h) / 2), self.l, self.l))
        self.ani2.setStartValue(1)
        self.ani2.setEndValue(0)

        self.setGroup = QParallelAnimationGroup(self)
        self.setGroup.addAnimation(self.ani)
        self.setGroup.addAnimation(self.ani2)
        self.setGroup.finished.connect(lambda: self.aniFinish())
        self.setGroup.start()

    def aniFinish(self):
        #self.setGroup.finished.disconnect()
        self.setGeometry(self._x, self._y, self.w, self.h)
        if not self.c:
            self.aniStart()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        super().mousePressEvent(ev)
        self.ani.setDuration(250)
        self.ani2.setDuration(250)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        self.ani.setDuration(750)
        self.ani2.setDuration(750)

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.c = False
        self.w = self.width()
        self.h = self.height()
        self._x = self.x()
        self._y = self.y()

        self.ani.setDuration(750)
        self.ani2.setDuration(750)

        self.setGroup.stop()
        self.aniStart()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setGroup.stop()
        self.opacity_effect.setOpacity(1)
        self.setGeometry(self._x, self._y, self.w, self.h)

app = QApplication(sys.argv)
window = Loading()
window.resize(1280, 720)
window.show()
window.startAni()

sys.exit(app.exec())
