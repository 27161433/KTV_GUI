from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGraphicsOpacityEffect, QVBoxLayout, QHBoxLayout, QScrollArea, QLineEdit, QMenu, QGraphicsDropShadowEffect, QTextEdit, QFrame, QProgressBar
from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase, QMovie, QResizeEvent, QMouseEvent, QKeyEvent, QAction, QCursor, QColor, QIcon, QWheelEvent, QPainter, QBrush, QPainterPath, QEnterEvent, QPen
from PySide6.QtCore import Qt, QRegularExpression, QUrl, QEasingCurve, QThread, Signal, QTimer, QPropertyAnimation, QPoint, Property, QPointF, QRect, QParallelAnimationGroup, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudio, QMediaFormat
from PySide6.QtMultimediaWidgets import QVideoWidget
from qframelesswindow import FramelessWindow, AcrylicWindow
from subprocess import Popen, PIPE, STDOUT
import yt_dlp as ytdl

import json
import requests
import os

class GetYT(QThread):
    updateGUI = Signal(str)
    def __init__(self):
        super().__init__()

        self.id = ''
        self.opt = {}
        self.progress0 = 0
        self.progress1 = 0
        self.finish0 = False
        self.finish1 = False

    def progressHook0(self, d):
        if d['status'] == 'downloading':
            downloaded = d['downloaded_bytes']
            if 'total_bytes' in d:
                total = d['total_bytes']
                if total == 0:
                    return
                self.progress0 = round(downloaded / total / 2 * 100)
            elif 'total_bytes_estimate' in d:
                total = d['total_bytes_estimate']
                if total == 0:
                    return
                self.progress0 = round(downloaded / total / 2 * 100)
        elif d['status'] == 'finished':
            self.finish0 = True
        self.updateGUI.emit(str(self.progress0))

    def progressHook1(self, d):
        if d['status'] == 'downloading':
            downloaded = d['downloaded_bytes']
            if 'total_bytes' in d:
                total = d['total_bytes']
                if total == 0:
                    return
                self.progress1 = round(downloaded / total / 2 * 100)
            elif 'total_bytes_estimate' in d:
                total = d['total_bytes_estimate']
                if total == 0:
                    return
                self.progress1 = round(downloaded / total / 2 * 100)
        elif d['status'] == 'finished':
            self.finish1 = True
        self.updateGUI.emit(str(self.progress0 + self.progress1))

    def run(self):
        filePath = f'./cache/yt/{self.id}.mp3'
        video_url = f'https://www.youtube.com/watch?v={self.id}'

        if not os.path.isfile(filePath):

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': filePath,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.progressHook0]
            }

            with ytdl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                
        filePath = f'./cache/yt/{self.id}.webm'
        if not os.path.isfile(filePath):

            ydl_opts = {
                'format': 'bestvideo/best',
                'outtmpl': filePath,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.progressHook1]
            }
            with ytdl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        self.opt = { "code": 2, "lyric": { "lrc": None, "tlyric": None } }


class Player(QThread):
    opt = Signal(str)
    sendSongData_opt = Signal(str)

    def __init__(self):
        super().__init__()
        self.output = ""

    def sendSongData(self, data: dict, status):
        path = "ncm"
        if data["type"] == 1:
            path = "yt"
        input_data = {
            "id": str(data["id"]),
            "title": data["title"],
            "img": f"./cache/{path}/{data['id']}.jpg",
            "dt": data["dt"],
            "artis": data["artis"],
            "lrc": data.get("lrc", None),
            "type": data["type"],
            "status": status
        }
        self.process.stdin.write(json.dumps(input_data) + '\n')
        self.process.stdin.flush()

        self.sendSongData_opt.emit("ok")

    def sendPause(self):
        self.process.stdin.write("pause" + '\n')
        self.process.stdin.flush()

    def sendReload(self):
        self.process.stdin.write("reload" + '\n')
        self.process.stdin.flush()

    def sendStop(self):
        self.process.stdin.write("stop" + '\n')
        self.process.stdin.flush()

    def sendClose(self):
        self.process.stdin.write("close" + '\n')
        self.process.stdin.flush()


    def run(self):
        self.output = ""
        self.process = Popen(["python", "player.py"], stdin=PIPE, stdout=PIPE, text=True)
        
        while True:
            o = self.process.stdout.readline().strip()
            if not o:
                break

            self.output += o

            self.opt.emit(o)
            print(o)

        self.process.wait()


class GetImg(QThread):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.data = bytes

    def run(self):
        response = requests.get(self.url)
        self.data = response.content


class GetSongList(QThread):
    progress_updated = Signal(str)

    def __init__(self, exe_path):
        super().__init__()
        self.exe_path = exe_path
        self.arguments = []
        self.output = ""

    def run(self):
        self.output = ""
        process = Popen([self.exe_path] + self.arguments, stdout=PIPE, universal_newlines=True)

        while True:
            o = process.stdout.readline().strip()
            if not o:
                break

            self.output += o

            self.progress_updated.emit(o)

        process.wait()


class LoadingIMG(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QPixmap("./img/loading_icon.png")
        self.setPixmap(self.image.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.setPixmap(self.image.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


class Loading(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()

        self.loop = 0

        self.image_label = LoadingIMG(self)
        self.animation = QPropertyAnimation(self.image_label, b"geometry")
        self.animation.setDuration(750)
        self.animation.finished.connect(self.nextLoop)

        self._size = min(self.width(), self.height())

    def startAni(self):
        self.animation.setDuration(750)
        self._size = min(self.width(), self.height())
        self.show()
        self.ani1()

    def stopAni(self):
        self.ani4()

    def nextLoop(self):
        match self.loop:
            case 0:
                self.ani2()
            case 1:
                self.ani3()
            case 2:
                self.ani2()
            case 3:
                self.hide()
        
    def ani1(self):
        self.loop = 0
        self._size = min(self.width(), self.height())
        self.l_size = max(self.height(), self.width())
        p = -round(self.l_size / 2)
        s = self.l_size * 2
        _s = self._size / 10 * 2
        self.animation.setStartValue(QRect(p, p, s, s))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.start()

    def ani2(self):
        self.loop = 1
        self._size = min(self.width(), self.height())
        s = self._size / 10 * 2
        _s = self._size / 10 * 4

        self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.start()

    def ani3(self):
        self.loop = 2
        self._size = min(self.width(), self.height())
        s = self._size / 10 * 4
        _s = self._size / 10 * 2

        self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(round((self.width() - _s) / 2), round((self.height() - _s) / 2), round(_s), round(_s)))
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.animation.start()

    def ani4(self):
        self.animation.stop()
        self.loop = 3
        self._size = min(self.width(), self.height())
        self.l_size = max(self.height(), self.width())
        s = self._size / 10 * 2
        p = -self.l_size
        _s = self.l_size * 3

        #self.animation.setStartValue(QRect(round((self.width() - s) / 2), round((self.height() - s) / 2), round(s), round(s)))
        self.animation.setEndValue(QRect(p, p, _s, _s))
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.setDuration(1000)
        self.animation.start()


class IconAni(QLabel):
    def __init__(self, img, parent=None):
        super().__init__(parent)

        self.l = 60

        self.c = False

        self.w = 50
        self.h = 50
        self._x = self.x()
        self._y = self.y()

        self.pix = QPixmap(img)

        self.setPixmap(self.pix.scaled(self.w, self.h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setStyleSheet("background: black; border-radius: 20px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.setPixmap(self.pix.scaled(self.width() - 10, self.height() - 10, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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


class SearchButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pix = QPixmap("./img/search_icon.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")
        icon = None
        pix = None

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        print("clicked")


class SettingsButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pix = QPixmap("./img/setting_icon.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        pix = None
        icon = None

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        print("clicked")


class SongListButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pix = QPixmap("./img/list_icon.png").scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        pix = None
        icon = None

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        print("clicked")


class Play_Pause_Button(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pause_pix = QPixmap("./img/pause_icon.png").scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        play_pix = QPixmap("./img/play_icon.png").scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.pause_icon = QIcon(pause_pix)
        self.play_icon = QIcon(play_pix)
        self.setIcon(self.pause_icon)
        self.setIconSize(pause_pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        self.pause = False

        pause_pix = None
        play_pix = None

    def setPlayer(self, player):
        self.player = player

    def init(self):
        self.pause = False
        self.setIcon(self.pause_icon)

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        self.player.sendPause()

    def pauseF(self):
        self.pause = not self.pause
        if self.pause:
            self.setIcon(self.play_icon)
        else:
            self.setIcon(self.pause_icon)


class Skip_Button(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        pix = QPixmap("./img/skip_icon.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        pix = None
        icon = None

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)


class Reload_Button(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pix = QPixmap("./img/reload_icon.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        pix = None
        icon = None


    def setPlayer(self, player):
        self.player = player

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        self.player.sendReload()


class Favorite_Button(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clicked.connect(self.__onClicked)
        pix = QPixmap("./img/favorite_icon.png").scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        icon = QIcon(pix)
        self.setIcon(icon)
        self.setIconSize(pix.size())
        self.resize(50, 50)
        self.setStyleSheet("background: black; border-radius: 25px;")

        pix = None
        icon = None

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        super().mousePressEvent(e)
        self.move(self.pos().x() + 5, self.pos().y() + 5)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        super().mouseReleaseEvent(e)
        self.move(self.pos().x() - 5, self.pos().y() - 5)

    def __onClicked(self):
        print("clicked")


class Line(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: gray; border-radius: 1px;")
        self.hide()


class SongItem(QWidget):
    addBtn_OnClicked = Signal(str, int)
    insertBtn_OnClicked = Signal(str, int)
    favoriteBtn_OnClicked = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self._type = 0
        self._id = ""

        self.img = QLabel(self)
        self.img.resize(116, 116)

        self.title = QLabel(self)
        self.title.setFont(QFont(fontName, 15))
        #self.title.setStyleSheet("background: blue;")
        self.title.setWordWrap(True)


        self.dt = QLabel(self)
        self.dt.setFont(QFont(fontName, 15))

        self.addSongBtn = QPushButton(self)
        self.addSongBtn.setText("點歌")
        self.addSongBtn.setFont(QFont(fontName, 15))
        self.addSongBtn.clicked.connect(self.addSongBtn_Clicked)
        #self.addSongBtn.setStyleSheet("background: yellow;")

        self.insertSongBtn = QPushButton(self)
        self.insertSongBtn.setText("插歌")
        self.insertSongBtn.setFont(QFont(fontName, 15))
        self.insertSongBtn.clicked.connect(self.insertSongBtn_Clicked)

        self.addFavoriteBtn = QPushButton(self)
        self.addFavoriteBtn.setText("加到最愛")
        self.addFavoriteBtn.setFont(QFont(fontName, 15))
        self.addFavoriteBtn.clicked.connect(self.addFavoriteBtn_Clicked)

        self.addSongBtn.adjustSize()
        self.insertSongBtn.adjustSize()
        self.addFavoriteBtn.adjustSize()

    def adj(self):
        self.dt.adjustSize()
        self.title.resize(self.width() - (5 + self.img.width() + 5 + self.dt.width() + 5), self.height() - self.addSongBtn.height() - 5)

        self.img.move(5, round((self.height() - self.img.height()) / 2))
        self.title.move(5 + self.img.width() + 5, 5)
        self.dt.move(self.width() - (self.dt.width() + 5), 5 + round((self.height() - self.dt.height()) / 2))
        self.addSongBtn.move(5 + self.img.width() + 5, self.height() - self.addSongBtn.height())
        self.insertSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width(), self.height() - self.addSongBtn.height())
        self.addFavoriteBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5, self.height() - self.addSongBtn.height())

    def addSongBtn_Clicked(self):
        self.addBtn_OnClicked.emit(self._id, self._type)

    def insertSongBtn_Clicked(self):
        self.insertBtn_OnClicked.emit(self._id, self._type)

    def addFavoriteBtn_Clicked(self):
        self.favoriteBtn_OnClicked.emit(self._id, self._type)

    def setImg(self, _img):
        self.pix = QPixmap()
        self.pix.loadFromData(_img)

        pix = self.pix.scaledToHeight(116, Qt.TransformationMode.SmoothTransformation)

        if self.pix.width() > self.pix.height():
            crop_size = min(pix.width(), pix.height())

            # 计算裁剪的起始位置，使其位于原始图像中心
            x = (pix.width() - crop_size) // 2
            y = (pix.height() - crop_size) // 2

            # 创建一个新的正方形 QPixmap 对象，并绘制带有圆角的矩形作为裁剪区域
            cropped_pixmap = QPixmap(crop_size, crop_size)
            cropped_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(cropped_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿

            rounded_rect = QPainterPath()
            rounded_rect.addRoundedRect(0, 0, crop_size, crop_size, 20, 20)
            painter.setClipPath(rounded_rect)

            # 将裁剪区域应用于原始图像，并绘制到新的 QPixmap 对象上
            painter.drawPixmap(0, 0, pix, x, y, crop_size, crop_size)

            painter.end()

            self.img.setPixmap(cropped_pixmap)
            cropped_pixmap = None
            painter = None
            rounded_rect = None

        else:
            rounded_pixmap = QPixmap(pix.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿
            brush = QBrush(pix)
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)

            # 绘制圆角矩形
            rect = rounded_pixmap.rect()
            painter.drawRoundedRect(rect, 20, 20)

            painter.end()
            self.img.setPixmap(rounded_pixmap)
            rounded_pixmap = None
            painter = None
            brush = None
        
        self.pix = None
        pix = None

    def setTitle(self, title):
        self.title.setText(title)

    def setDt(self, dt):
        self.dt.setText(dt)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()


class FavoriteSongItem(QWidget):
    addBtn_OnClicked = Signal(str, int)
    insertBtn_OnClicked = Signal(str, int)
    delBtn_OnClicked = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self._type = 0
        self._id = ""

        self.img = QLabel(self)
        self.img.resize(116, 116)

        self.title = QLabel(self)
        self.title.setFont(QFont(fontName, 15))
        #self.title.setStyleSheet("background: blue;")
        self.title.setWordWrap(True)

        self.dt = QLabel(self)
        self.dt.setFont(QFont(fontName, 15))

        self.addSongBtn = QPushButton(self)
        self.addSongBtn.setText("點歌")
        self.addSongBtn.setFont(QFont(fontName, 15))
        self.addSongBtn.clicked.connect(self.addSongBtn_Clicked)
        #self.addSongBtn.setStyleSheet("background: yellow;")

        self.insertSongBtn = QPushButton(self)
        self.insertSongBtn.setText("插歌")
        self.insertSongBtn.setFont(QFont(fontName, 15))
        self.insertSongBtn.clicked.connect(self.insertSongBtn_Clicked)

        self.delSongBtn = QPushButton(self)
        self.delSongBtn.setText("刪除")
        self.delSongBtn.setFont(QFont(fontName, 15))
        self.delSongBtn.clicked.connect(self.delSongBtn_Clicked)

        self.addSongBtn.adjustSize()
        self.insertSongBtn.adjustSize()
        self.delSongBtn.adjustSize()

    def adj(self):
        self.dt.adjustSize()
        self.title.resize(self.width() - (5 + self.img.width() + 5 + self.dt.width() + 5), self.height() - self.addSongBtn.height() - 5)

        self.img.move(5, round((self.height() - self.img.height()) / 2))
        self.title.move(5 + self.img.width() + 5, 5)
        self.dt.move(self.width() - (self.dt.width() + 5), 5 + round((self.height() - self.dt.height()) / 2))
        self.addSongBtn.move(5 + self.img.width() + 5, self.height() - self.addSongBtn.height())
        self.insertSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width(), self.height() - self.addSongBtn.height())
        self.delSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5, self.height() - self.addSongBtn.height())

    def addSongBtn_Clicked(self):
        self.addBtn_OnClicked.emit(self._id, self._type)

    def insertSongBtn_Clicked(self):
        self.insertBtn_OnClicked.emit(self._id, self._type)

    def delSongBtn_Clicked(self):
        self.delBtn_OnClicked.emit(self._id, self._type)

    def setImg(self, _img):
        self.pix = QPixmap()
        self.pix.loadFromData(_img)

        pix = self.pix.scaledToHeight(116, Qt.TransformationMode.SmoothTransformation)

        if self.pix.width() > self.pix.height():
            crop_size = min(pix.width(), pix.height())

            # 计算裁剪的起始位置，使其位于原始图像中心
            x = (pix.width() - crop_size) // 2
            y = (pix.height() - crop_size) // 2

            # 创建一个新的正方形 QPixmap 对象，并绘制带有圆角的矩形作为裁剪区域
            cropped_pixmap = QPixmap(crop_size, crop_size)
            cropped_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(cropped_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿

            rounded_rect = QPainterPath()
            rounded_rect.addRoundedRect(0, 0, crop_size, crop_size, 20, 20)
            painter.setClipPath(rounded_rect)

            # 将裁剪区域应用于原始图像，并绘制到新的 QPixmap 对象上
            painter.drawPixmap(0, 0, pix, x, y, crop_size, crop_size)

            painter.end()

            self.img.setPixmap(cropped_pixmap)
            cropped_pixmap = None
            painter = None
            rounded_rect = None

        else:
            rounded_pixmap = QPixmap(pix.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿
            brush = QBrush(pix)
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)

            # 绘制圆角矩形
            rect = rounded_pixmap.rect()
            painter.drawRoundedRect(rect, 20, 20)

            painter.end()
            self.img.setPixmap(rounded_pixmap)
            rounded_pixmap = None
            painter = None
            brush = None
        
        self.pix = None
        pix = None

    def setTitle(self, title):
        self.title.setText(title)

    def setDt(self, dt):
        self.dt.setText(dt)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()


class SongList_SongItem(QWidget):
    delBtn_OnClicked = Signal(int)
    insertBtn_OnClicked = Signal(str, int)
    favoriteBtn_OnClicked = Signal(str, int)
    addSongBtn_OnClicked = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self._type = 0
        self._id = ""
        self.n = 0
        self.favorite_mode = False

        self.img = QLabel(self)
        self.img.resize(116, 116)

        self.progress_bar = QFrame(self)
        self.progress_bar.setStyleSheet("background: #0099ff; border-radius: 2px;")
        self.progress_bar.resize(1, 4)

        self.loadingWidget = QWidget(self)
        self.loadingWidget.resize(116, 116)

        self.loading = Loading(self.loadingWidget)
        self.loading.resize(self.loadingWidget.size())

        self.title = QLabel(self)
        self.title.setFont(QFont(fontName, 15))
        #self.title.setStyleSheet("background: blue;")
        self.title.setWordWrap(True)

        self.dt = QLabel(self)
        self.dt.setFont(QFont(fontName, 15))

        self.addSongBtn = QPushButton(self)
        self.addSongBtn.setText("點歌")
        self.addSongBtn.setFont(QFont(fontName, 15))
        self.addSongBtn.clicked.connect(self.addSongBtn_Clicked)
        #self.addSongBtn.setStyleSheet("background: yellow;")

        self.insertSongBtn = QPushButton(self)
        self.insertSongBtn.setText("插歌")
        self.insertSongBtn.setFont(QFont(fontName, 15))
        self.insertSongBtn.clicked.connect(self.insertSongBtn_Clicked)

        self.addFavoriteBtn = QPushButton(self)
        self.addFavoriteBtn.setText("加到最愛")
        self.addFavoriteBtn.setFont(QFont(fontName, 15))
        self.addFavoriteBtn.clicked.connect(self.addFavoriteBtn_Clicked)

        self.delSongBtn = QPushButton(self)
        self.delSongBtn.setText("刪除")
        self.delSongBtn.setFont(QFont(fontName, 15))
        self.delSongBtn.clicked.connect(self.delSongBtn_Clicked)

        self.progress_bar_ani = QPropertyAnimation(self.progress_bar, b"geometry")
        self.progress_bar_ani.setDuration(750)
        self.progress_bar_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.addSongBtn.adjustSize()
        self.insertSongBtn.adjustSize()
        self.addFavoriteBtn.adjustSize()
        self.delSongBtn.adjustSize()

    def setDownload(self):
        self.loading.show()
        self.progress_bar.show()
        self.loading.startAni()

    def setReady(self):
        self.loading.stopAni()
        self.progress_bar.hide()
    
    def setFavoriteMode(self):
        self.favorite_mode = True
        self.addFavoriteBtn.hide()

    def setProgress_bar(self, v):
        self.progress_bar_ani.stop()
        self.progress_bar_ani.setEndValue(QRect(5 + round((self.img.width() - 100) / 2), round((self.height() - 4) / 4 * 3), v, 4))
        self.progress_bar_ani.start()

    def setPlay(self):
        self.title.setStyleSheet("color: #0099ff;")
        self.dt.setStyleSheet("color: #0099ff;")
        self.delSongBtn.setDisabled(True)
        self.delSongBtn.setStyleSheet("color: #c4c4c4;")


    def setAlreadyPlay(self):
        self.title.setStyleSheet("color: #c4c4c4;")
        self.dt.setStyleSheet("color: #c4c4c4;")

    def adj(self):
        self.dt.adjustSize()
        self.title.resize(self.width() - (5 + self.img.width() + 5 + self.dt.width() + 5), self.height() - self.addSongBtn.height() - 5)

        self.loadingWidget.move(5, round((self.height() - self.img.height()) / 2))

        self.progress_bar.move(5 + round((self.img.width() - 100) / 2), round((self.height() - 4) / 4 * 3))
        self.img.move(5, round((self.height() - self.img.height()) / 2))
        self.title.move(5 + self.img.width() + 5, 5)
        self.dt.move(self.width() - (self.dt.width() + 5), 5 + round((self.height() - self.dt.height()) / 2))
        self.addSongBtn.move(5 + self.img.width() + 5, self.height() - self.addSongBtn.height())
        self.insertSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width(), self.height() - self.addSongBtn.height())
        if self.favorite_mode:
            self.delSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5, self.height() - self.addSongBtn.height())
        else:
            self.addFavoriteBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5, self.height() - self.addSongBtn.height())
            self.delSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5 + self.addFavoriteBtn.width() + 5, self.height() - self.addSongBtn.height())

    def delSongBtn_Clicked(self):
        self.delBtn_OnClicked.emit(self.n)

    def addSongBtn_Clicked(self):
        self.addSongBtn_OnClicked.emit(self._id, self._type)

    def insertSongBtn_Clicked(self):
        self.insertBtn_OnClicked.emit(self._id, self._type)

    def addFavoriteBtn_Clicked(self):
        self.favoriteBtn_OnClicked.emit(self._id, self._type)

    def setImg(self, _img):
        self.pix = QPixmap()
        self.pix.loadFromData(_img)

        pix = self.pix.scaledToHeight(116, Qt.TransformationMode.SmoothTransformation)

        if self.pix.width() > self.pix.height():
            crop_size = min(pix.width(), pix.height())

            # 计算裁剪的起始位置，使其位于原始图像中心
            x = (pix.width() - crop_size) // 2
            y = (pix.height() - crop_size) // 2

            # 创建一个新的正方形 QPixmap 对象，并绘制带有圆角的矩形作为裁剪区域
            cropped_pixmap = QPixmap(crop_size, crop_size)
            cropped_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(cropped_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿

            rounded_rect = QPainterPath()
            rounded_rect.addRoundedRect(0, 0, crop_size, crop_size, 20, 20)
            painter.setClipPath(rounded_rect)

            # 将裁剪区域应用于原始图像，并绘制到新的 QPixmap 对象上
            painter.drawPixmap(0, 0, pix, x, y, crop_size, crop_size)

            painter.end()

            self.img.setPixmap(cropped_pixmap)
            cropped_pixmap = None
            painter = None
            rounded_rect = None

        else:
            rounded_pixmap = QPixmap(pix.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿
            brush = QBrush(pix)
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)

            # 绘制圆角矩形
            rect = rounded_pixmap.rect()
            painter.drawRoundedRect(rect, 20, 20)

            painter.end()
            self.img.setPixmap(rounded_pixmap)
            rounded_pixmap = None
            painter = None
            brush = None
        
        self.pix = None
        pix = None

    def setTitle(self, title):
        self.title.setText(title)

    def setDt(self, dt):
        self.dt.setText(dt)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()

class Favorites_SongItem(QWidget):
    delBtn_OnClicked = Signal(str, int)
    insertBtn_OnClicked = Signal(str)
    addSongBtn_OnClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self._type = 0
        self.n = 0
        self._id = ""
        self._title = ""
        self.favorite_mode = False

        self.img = QLabel(self)
        self.img.resize(116, 116)

        self.progress_bar = QFrame(self)
        self.progress_bar.setStyleSheet("background: #0099ff; border-radius: 2px;")
        self.progress_bar.resize(1, 4)

        self.loadingWidget = QWidget(self)
        self.loadingWidget.resize(116, 116)

        self.loading = Loading(self.loadingWidget)
        self.loading.resize(self.loadingWidget.size())

        self.title = QLabel(self)
        self.title.setFont(QFont(fontName, 15))
        #self.title.setStyleSheet("background: blue;")
        self.title.setWordWrap(True)

        self.dt = QLabel(self)
        self.dt.setFont(QFont(fontName, 15))

        self.addSongBtn = QPushButton(self)
        self.addSongBtn.setText("點歌")
        self.addSongBtn.setFont(QFont(fontName, 15))
        self.addSongBtn.clicked.connect(self.addSongBtn_Clicked)
        #self.addSongBtn.setStyleSheet("background: yellow;")

        self.insertSongBtn = QPushButton(self)
        self.insertSongBtn.setText("插歌")
        self.insertSongBtn.setFont(QFont(fontName, 15))
        self.insertSongBtn.clicked.connect(self.insertSongBtn_Clicked)

        self.delSongBtn = QPushButton(self)
        self.delSongBtn.setText("刪除")
        self.delSongBtn.setFont(QFont(fontName, 15))
        self.delSongBtn.clicked.connect(self.delSongBtn_Clicked)

        self.progress_bar_ani = QPropertyAnimation(self.progress_bar, b"geometry")
        self.progress_bar_ani.setDuration(750)
        self.progress_bar_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.addSongBtn.adjustSize()
        self.insertSongBtn.adjustSize()
        self.delSongBtn.adjustSize()

    def setDownload(self):
        self.loading.show()
        self.progress_bar.show()
        self.loading.startAni()

    def setReady(self):
        self.loading.stopAni()
        self.progress_bar.hide()
    
    def setProgress_bar(self, v):
        self.progress_bar_ani.stop()
        self.progress_bar_ani.setEndValue(QRect(5 + round((self.img.width() - 100) / 2), round((self.height() - 4) / 4 * 3), v, 4))
        self.progress_bar_ani.start()

    def setPlay(self):
        self.title.setStyleSheet("color: #0099ff;")
        self.dt.setStyleSheet("color: #0099ff;")
        self.delSongBtn.setDisabled(True)
        self.delSongBtn.setStyleSheet("color: #c4c4c4;")


    def setAlreadyPlay(self):
        self.title.setStyleSheet("color: #c4c4c4;")
        self.dt.setStyleSheet("color: #c4c4c4;")

    def adj(self):
        self.dt.adjustSize()
        self.title.resize(self.width() - (5 + self.img.width() + 5 + self.dt.width() + 5), self.height() - self.addSongBtn.height() - 5)

        self.loadingWidget.move(5, round((self.height() - self.img.height()) / 2))

        self.progress_bar.move(5 + round((self.img.width() - 100) / 2), round((self.height() - 4) / 4 * 3))
        self.img.move(5, round((self.height() - self.img.height()) / 2))
        self.title.move(5 + self.img.width() + 5, 5)
        self.dt.move(self.width() - (self.dt.width() + 5), 5 + round((self.height() - self.dt.height()) / 2))
        self.addSongBtn.move(5 + self.img.width() + 5, self.height() - self.addSongBtn.height())
        self.insertSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width(), self.height() - self.addSongBtn.height())
        self.delSongBtn.move(5 + self.img.width() + 5 + 5 + self.addSongBtn.width() + self.insertSongBtn.width() + 5, self.height() - self.addSongBtn.height())
    def delSongBtn_Clicked(self):
        self.delBtn_OnClicked.emit(self._id, self.n)

    def addSongBtn_Clicked(self):
        self.addSongBtn_OnClicked.emit(self._id)

    def insertSongBtn_Clicked(self):
        self.insertBtn_OnClicked.emit(self._id)

    def setImg(self, _img):
        self.pix = QPixmap()
        self.pix.loadFromData(_img)

        pix = self.pix.scaledToHeight(116, Qt.TransformationMode.SmoothTransformation)

        if self.pix.width() > self.pix.height():
            crop_size = min(pix.width(), pix.height())

            # 计算裁剪的起始位置，使其位于原始图像中心
            x = (pix.width() - crop_size) // 2
            y = (pix.height() - crop_size) // 2

            # 创建一个新的正方形 QPixmap 对象，并绘制带有圆角的矩形作为裁剪区域
            cropped_pixmap = QPixmap(crop_size, crop_size)
            cropped_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(cropped_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿

            rounded_rect = QPainterPath()
            rounded_rect.addRoundedRect(0, 0, crop_size, crop_size, 20, 20)
            painter.setClipPath(rounded_rect)

            # 将裁剪区域应用于原始图像，并绘制到新的 QPixmap 对象上
            painter.drawPixmap(0, 0, pix, x, y, crop_size, crop_size)

            painter.end()

            self.img.setPixmap(cropped_pixmap)
            cropped_pixmap = None
            painter = None
            rounded_rect = None

        else:
            rounded_pixmap = QPixmap(pix.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿
            brush = QBrush(pix)
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)

            # 绘制圆角矩形
            rect = rounded_pixmap.rect()
            painter.drawRoundedRect(rect, 20, 20)

            painter.end()
            self.img.setPixmap(rounded_pixmap)
            rounded_pixmap = None
            painter = None
            brush = None
        
        self.pix = None
        pix = None

    def setTitle(self, title):
        self.title.setText(title)

    def setDt(self, dt):
        self.dt.setText(dt)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()


class ListItem(QWidget):
    clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.newAdd = False

        self.enter = QFrame(self)
        self.enter.setStyleSheet("background: rgba(200, 200, 200, 0.3); border-radius: 10px;")
        self.enter.resize(self.size())
        self.enter.hide()

        self.press = QFrame(self)
        self.press.setStyleSheet("background: rgba(200, 200, 200, 0.3); border-radius: 10px;")
        self.press.resize(self.size())
        self.press.hide()

        self.title = QLabel(self)
        self.title.setFont(QFont(fontName, 15))
        #self.title.setStyleSheet("background: blue;")
        self.title.setWordWrap(True)
        self.title.setStyleSheet("background: transparent;")


        self.img = QLabel(self)
        self.img.resize(60, 60)
        self.img.setStyleSheet("background: transparent;")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.press.show()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.press.hide()
        self.clicked.emit(self.title.text())

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.enter.show()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.enter.hide()

    def adj(self):
        self.title.resize(self.width() - (5 + self.img.width() + 5 + 5), self.height() - 10)
        self.enter.resize(self.size())
        self.press.resize(self.size())

        self.img.move(5, round((self.height() - self.img.height()) / 2))
        self.title.move(5 + self.img.width() + 5, 5)

    def _setImg(self, _img):
        self.pix = QPixmap(_img).scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
        self.img.setPixmap(self.pix)

        self.pix = None
        self.newAdd = True

    def setImg(self, _img):
        self.pix = QPixmap()
        self.pix.loadFromData(_img)

        pix = self.pix.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)

        if self.pix.width() > self.pix.height():
            crop_size = min(pix.width(), pix.height())

            # 计算裁剪的起始位置，使其位于原始图像中心
            x = (pix.width() - crop_size) // 2
            y = (pix.height() - crop_size) // 2

            # 创建一个新的正方形 QPixmap 对象，并绘制带有圆角的矩形作为裁剪区域
            cropped_pixmap = QPixmap(crop_size, crop_size)
            cropped_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(cropped_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿

            rounded_rect = QPainterPath()
            rounded_rect.addRoundedRect(0, 0, crop_size, crop_size, 20, 20)
            painter.setClipPath(rounded_rect)

            # 将裁剪区域应用于原始图像，并绘制到新的 QPixmap 对象上
            painter.drawPixmap(0, 0, pix, x, y, crop_size, crop_size)

            painter.end()

            self.img.setPixmap(cropped_pixmap)
            cropped_pixmap = None
            painter = None
            rounded_rect = None

        else:
            rounded_pixmap = QPixmap(pix.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿
            brush = QBrush(pix)
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)

            # 绘制圆角矩形
            rect = rounded_pixmap.rect()
            painter.drawRoundedRect(rect, 20, 20)

            painter.end()
            self.img.setPixmap(rounded_pixmap)
            rounded_pixmap = None
            painter = None
            brush = None
        
        self.pix = None
        pix = None

    def setTitle(self, title):
        self.title.setText(title)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()


class SAWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets = []
        self.mainWidget = QWidget(self)
        self.hide()

        self.up = False
        self.down = True

        self.mainWidgetAni = QPropertyAnimation(self.mainWidget, b"pos")
        self.mainWidgetAni.setDuration(500)
        self.mainWidgetAni.setEasingCurve(QEasingCurve.Type.OutQuart)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        h = 0
        for i in self.widgets:
            h += i["h"]
        self.mainWidget.resize(self.width(), h)
        for child in self.mainWidget.findChildren(QWidget):
            if child.objectName() == "data":
                child.resize(self.width() ,child.height())

    def initForAddFavorites(self):
        self.up = False
        self.down = True
        self.widgets = []
        self.mainWidget.move(0, 0)

        for child in self.mainWidget.findChildren(QWidget):
            if child.objectName() == "data":
                child.clicked.disconnect()
                child.deleteLater()

    def initForFavorites(self):
        self.up = False
        self.down = True
        self.widgets = []
        self.mainWidget.move(0, 0)
        for child in self.mainWidget.findChildren(QWidget):
            if child.objectName() == "data":
                child.addSongBtn_OnClicked.disconnect()
                child.insertBtn_OnClicked.disconnect()
                child.delBtn_OnClicked.disconnect()
                child.deleteLater()

    def init(self):
        self.up = False
        self.down = True
        self.widgets = []
        self.mainWidget.move(0, 0)
        for child in self.mainWidget.findChildren(QWidget):
            if child.objectName() == "data":
                child.addBtn_OnClicked.disconnect()
                child.insertBtn_OnClicked.disconnect()
                child.favoriteBtn_OnClicked.disconnect()
                child.deleteLater()
    
    def delSong(self, n):

        g = -1
        _h = 0

        def _da(self, a, h):
            a.deleteLater()
            self.mainWidget.resize(self.width(), h)


        for i in range(len(self.widgets)):
            
            if self.widgets[i]["o"].n == n:
                self.widgets[i]["o"].deleteLater()
                g = i
            else:
                if self.widgets[i]["o"].pos().y != _h:
                    _ani = QPropertyAnimation(self.widgets[i]["o"], b"pos", self)
                    _ani.setDuration(750)
                    _ani.setEasingCurve(QEasingCurve.Type.OutQuart)
                    #ani.setStartValue(QPoint(0, self.mainWidget.height() + widget.height()))
                    _ani.setEndValue(QPoint(0, _h))
                    _ani.start()
                    if i == len(self.widgets) - 1:
                        _ani.finished.connect(lambda _ani=_ani: _da(self, _ani, _h))
                    else:
                        _ani.finished.connect(lambda _ani=_ani: self.delAni(_ani))

                _h += self.widgets[i]["h"]


            
        if g == -1:
            return g
        del self.widgets[g]
        return g


    def addWidget(self, widget: QWidget, _id=None):
        h = 0
        for i in self.widgets:
            h += i["h"]
        self.widgets.append({
            "o": widget,
            "w": widget.width(),
            "h": widget.height(),
            "id": _id
        })
        widget.resize(self.width(), widget.height())
        widget.setParent(self.mainWidget)
        widget.setObjectName("data")
        widget.move(0, h)
        widget.show()
        self.mainWidget.resize(self.width(), h + widget.height())

    def _addWidget(self, widget: QWidget, _id=None):
        h = 0
        for i in self.widgets:
            h += i["h"]
        self.widgets.append({
            "o": widget,
            "w": widget.width(),
            "h": widget.height(),
            "id": _id
        })
        widget.resize(self.width(), widget.height())
        widget.setParent(self.mainWidget)
        widget.setObjectName("data")
        widget.move(0, self.mainWidget.height() + widget.height())
        widget.show()
        h2 = max(h + widget.height(), self.height())
        self.mainWidget.resize(self.width(), h2)

        ani = QPropertyAnimation(widget, b"pos", self)
        ani.setDuration(750)
        ani.setEasingCurve(QEasingCurve.Type.OutQuart)
        ani.setStartValue(QPoint(0, self.mainWidget.height() + widget.height()))
        ani.setEndValue(QPoint(0, h))
        ani.start()
        ani.finished.connect(lambda: self.setDownload(ani, widget))

    def setDownload(self, a, widget):
        a.deleteLater()
        widget.setDownload()

        if widget._type == 0:
            if os.path.isfile(f"./cache/ncm/{widget._id}.mp3"):
                widget.setReady()
        else:
            if os.path.isfile(f"./cache/yt/{widget._id}.mp3") and os.path.isfile(f"./cache/yt/{widget._id}.webm"):
                widget.setReady()


    def _insertWidget(self, widget: QWidget, index, _id=None):
        h = 0
        th = 0
        for i in range(len(self.widgets)):
            if i < index:
                h += self.widgets[i]["h"]
            th += self.widgets[i]["h"]
        self.widgets.insert(index, {
            "o": widget,
            "w": widget.width(),
            "h": widget.height(),
            "id": _id
        })
        widget.resize(self.width(), widget.height())
        widget.setParent(self.mainWidget)
        widget.setObjectName("data")
        widget.move(0, self.mainWidget.height() + widget.height())
        widget.show()
        h2 = max(th + widget.height(), self.height())
        self.mainWidget.resize(self.width(), h2)

        ani = QPropertyAnimation(widget, b"pos", self)
        ani.setDuration(750)
        ani.setEasingCurve(QEasingCurve.Type.OutQuart)
        ani.setStartValue(QPoint(0, self.mainWidget.height() + widget.height()))
        ani.setEndValue(QPoint(0, h))
        ani.start()
        ani.finished.connect(lambda: self.setDownload(ani, widget))

        for i in range(len(self.widgets)):
            if i <= index:
                continue
            _h = 0
            for j in range(len(self.widgets)):
                if j >= i:
                    break
                _h += self.widgets[j]["h"]
            _ani = QPropertyAnimation(self.widgets[i]["o"], b"pos", self)
            _ani.setDuration(750)
            _ani.setEasingCurve(QEasingCurve.Type.OutQuart)
            #ani.setStartValue(QPoint(0, self.mainWidget.height() + widget.height()))
            _ani.setEndValue(QPoint(0, _h))
            _ani.start()
            _ani.finished.connect(lambda: self.delAni(_ani))

    def setPlay(self, np):
        def update(self, timer):
            if len(self.widgets) > np:
                if np > 0:
                    self.widgets[np - 1]["o"].setAlreadyPlay()
                self.widgets[np]["o"].setPlay()
                timer.stop()


        timer = QTimer(self)
        timer.timeout.connect(lambda: update(self, timer))
        timer.start(100)

    def setAlreadyPlay(self, np):
        self.widgets[np]["o"].setAlreadyPlay()

    def setProgressBar(self, _id, v):
        for i in self.widgets:
            if str(i["id"]) == str(_id):
                i["o"].setProgress_bar(v)

    def setReady(self, _id):
        for i in self.widgets:
            if i["id"] == _id:
                i["o"].setReady()


    def delAni(self, a):
        a.deleteLater()

    def wheelEvent(self, event: QWheelEvent) -> None:
        #super().wheelEvent(event)
        angle_y = event.angleDelta().y()

        self.mainWidgetAni.stop()

        if angle_y > 0:
            y = self.mainWidget.pos().y() + 200
            if y >= 0:
                y = 0
                self.up = False
            self.down = True
            self.mainWidgetAni.setEndValue(QPoint(0, y))
            self.mainWidgetAni.start()
        elif angle_y < 0:
            y = self.mainWidget.pos().y() - 200
            if y <= -(self.mainWidget.height() - self.height()):
                y = -(self.mainWidget.height() - self.height())
                self.down = False

            self.up = True
            self.mainWidgetAni.setEndValue(QPoint(0, y))
            self.mainWidgetAni.start()


class Icon(QLabel):
    ani = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.t = ""

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        self.ani.emit(self.t)


class SongList(QWidget):
    searchReturn = Signal()
    delSongBtn_OnClicked = Signal(int)
    insertBtn_OnClicked = Signal(str, int)
    favoriteBtn_OnClicked = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]
        self.hide()

        self.list = SAWidget(self)
        self.n = 0

    def adj(self):
        self.list.setGeometry(10, 3, self.width() - 20, self.height() - 7)

    def resizeEvent(self, event: QResizeEvent) -> None:
        #super().resizeEvent(event)
        self.adj()

    def insertList(self, data, np):
        item = SongList_SongItem()

        item._id = str(data["id"])
        item._type = data["type"]
        item.resize(self.width(), 126)

        item.setTitle(f"{data['artis']} - {data['title']}")
        dt = data["dt"] // 1000
        s = dt
        m = 0
        if dt > 60:
            s = dt % 60
            m = dt // 60

        item.setDt(f"{str(m).zfill(2)}:{str(s).zfill(2)}")
        item.adj()
        item.delBtn_OnClicked.connect(self.delSongBtn_Clicked)
        item.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        item.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)

        getImg = GetImg(data["img"])
        getImg.finished.connect(lambda: setImg(getImg))
        getImg.start()

        def setImg(t):
            item.setImg(t.data)
            t.data = None
            t.deleteLater()
            self.list.show()
            item.n = self.n
            self.list._insertWidget(item, np + 1, _id=str(data["id"]))
            self.n += 1
        
    def addList(self, data):
        item = SongList_SongItem()

        item._id = str(data["id"])
        item._type = data["type"]
        item.resize(self.width(), 126)

        item.setTitle(f"{data['artis']} - {data['title']}")
        dt = data["dt"] // 1000
        s = dt
        m = 0
        if dt > 60:
            s = dt % 60
            m = dt // 60

        item.setDt(f"{str(m).zfill(2)}:{str(s).zfill(2)}")
        item.adj()
        item.delBtn_OnClicked.connect(self.delSongBtn_Clicked)
        item.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        item.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)

        getImg = GetImg(data["img"])
        getImg.finished.connect(lambda: setImg(getImg))
        getImg.start()

        def setImg(t):
            item.setImg(t.data)
            t.data = None
            t.deleteLater()
            self.list.show()
            item.n = self.n
            self.list._addWidget(item, _id=str(data["id"]))     
            self.n += 1

    def setPlay(self, np):
        self.list.setPlay(np)

    def setProgressBar(self, _id, v):
        self.list.setProgressBar(_id, v)

    def setAlreadyPlay(self, np):
        self.list.setAlreadyPlay(np)

    def setReady(self, _id):
        self.list.setReady(_id)

    def delSongBtn_Clicked(self, n):
        g = self.list.delSong(n)
        if g != -1:
            self.delSongBtn_OnClicked.emit(g)

    def insertSongBtn_Clicked(self, _id, _type):
        self.insertBtn_OnClicked.emit(_id, _type)

    def addFavoriteBtn_Clicked(self, _id, _type):
        self.favoriteBtn_OnClicked.emit(_id, _type)


class SearchList(QWidget):
    searchReturn = Signal()
    addBtn_OnClicked = Signal(str, int)
    insertBtn_OnClicked = Signal(str, int)
    favoriteBtn_OnClicked = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.page = "ncm"
        self.new = False
        self.ncmReady = False
        self.ytReady = False
        self.yt = []
        self.ncm = []

        self.hide()

        self.__title = QLabel(self)
        self.__title.setText("來源選擇:")
        self.__title.setFont(QFont(fontName, 20))
        self.__title.adjustSize()

        self.line = Line(self)

        self.ncmIcon = Icon(self)
        self.ncmIcon.t = "ncm"
        ncmIcon = QPixmap("./img/ncm_icon.png").scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
        self.ncmIcon.setPixmap(ncmIcon)
        self.ncmIcon.ani.connect(self.pageAni)
        ncmIcon = None

        self.ytIcon = Icon(self)
        self.ytIcon.t = "yt"
        ytIcon = QPixmap("./img/youtube_icon.png").scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
        self.ytIcon.setPixmap(ytIcon)
        self.ytIcon.ani.connect(self.pageAni)
        ytIcon = None

        self.chooseIcon = QLabel(self)
        chooseIcon = QPixmap("./img/loading_icon.png").scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
        self.chooseIcon.setPixmap(chooseIcon)
        chooseIcon = None

        self.ncmList = SAWidget(self)

        self.ytList = SAWidget(self)

        self.loading = Loading(self)

        self.__title_ani = QPropertyAnimation(self.__title, b"pos")
        self.__title_ani.setDuration(750)
        self.__title_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.line_ani = QPropertyAnimation(self.line, b"geometry")
        self.line_ani.setDuration(750)
        self.line_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ncmIcon_ani = QPropertyAnimation(self.ncmIcon, b"pos")
        self.ncmIcon_ani.setDuration(750)
        self.ncmIcon_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ytIcon_ani = QPropertyAnimation(self.ytIcon, b"pos")
        self.ytIcon_ani.setDuration(750)
        self.ytIcon_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.chooseIcon_ani = QPropertyAnimation(self.chooseIcon, b"pos")
        self.chooseIcon_ani.setDuration(750)
        self.chooseIcon_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.chooseIcon_ani2 = QPropertyAnimation(self.chooseIcon, b"pos")
        self.chooseIcon_ani2.setDuration(750)
        self.chooseIcon_ani2.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ncmList_ani = QPropertyAnimation(self.ncmList, b"pos")
        self.ncmList_ani.setDuration(750)
        self.ncmList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ytList_ani = QPropertyAnimation(self.ytList, b"pos")
        self.ytList_ani.setDuration(750)
        self.ytList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.newPage_ani_group = QParallelAnimationGroup(self)
        self.newPage_ani_group.addAnimation(self.__title_ani)
        self.newPage_ani_group.addAnimation(self.line_ani)
        self.newPage_ani_group.addAnimation(self.ncmIcon_ani)
        self.newPage_ani_group.addAnimation(self.ytIcon_ani)
        self.newPage_ani_group.addAnimation(self.chooseIcon_ani)

        self.pageChange_ani_group = QParallelAnimationGroup(self)
        self.pageChange_ani_group.addAnimation(self.ncmList_ani)
        self.pageChange_ani_group.addAnimation(self.ytList_ani)
        self.pageChange_ani_group.addAnimation(self.chooseIcon_ani2)


    def adj(self):
        self.ncmList.resize(self.width() - 20, self.height() - (10 + self.__title.height() + 10 + 10 + 2))
        self.ytList.resize(self.width() - 20, self.height() - (10 + self.__title.height() + 10 + 10 + 2))
        self.loading.resize(self.size())

        title_x = -self.__title.width()
        title_y = 10

        ncmIcon_x = 30 + self.__title.width()
        ncmIcon_y = -40

        ytIcon_x = 40 + self.__title.width() + self.ncmIcon.width()
        ytIcon_y = -40

        line_w = 1
        line_h = 2
        line_x = 10
        line_y = 10 + self.__title.height() + 10

        chooseIcon_x = 10 + self.__title.width() + 0
        chooseIcon_y = -60

        ncmList_x = 10
        ncmList_y = self.height()

        ytList_x = self.width()
        ytList_y = self.height()

        if self.new:
            title_x = 20
            ncmIcon_y = 10
            ytIcon_y = 10
            line_w = self.width() - 20
            chooseIcon_x = 20 + self.__title.width() + 0
            chooseIcon_y = 0
            ncmList_y = 10 + self.__title.height() + 10 + 10
            ytList_y = 10 + self.__title.height() + 10 + 10

        self.line.setGeometry(line_x, line_y, line_w, line_h)

        self.__title.move(title_x, title_y)

        self.ncmIcon.move(ncmIcon_x, ncmIcon_y)
        self.ytIcon.move(ytIcon_x, ytIcon_y)



        if self.page == "yt":
            ncmList_x = -self.width()
            ytList_x = 10
            chooseIcon_x = 20 + self.__title.width() + 50

        self.ncmList.move(ncmList_x, ncmList_y)
        self.ytList.move(ytList_x, ytList_y)

        self.chooseIcon.move(chooseIcon_x, chooseIcon_y)


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()

    def pageAni(self, t):
        self.pageChange_ani_group.stop()
        ytList_x = self.width()
        ytList_y = 10 + self.__title.height() + 10 + 10

        ncmList_x = 10
        ncmList_y = 10 + self.__title.height() + 10 + 10

        chooseIcon_x = 20 + self.__title.width()
        chooseIcon_y = 0

        if t == "yt":
            ytList_x = 10
            ncmList_x = -self.width()
            chooseIcon_x = 20 + self.__title.width() + 50
            self.page = "yt"
        else:
            self.page = "ncm"


        self.ytList_ani.setEndValue(QPoint(ytList_x, ytList_y))

        self.ncmList_ani.setEndValue(QPoint(ncmList_x, ncmList_y))

        self.chooseIcon_ani2.setEndValue(QPoint(chooseIcon_x, chooseIcon_y))

        self.pageChange_ani_group.start()

    def loadingAniStart(self):
        self.loading.startAni()

        if not self.new:
            self.new = True
            self.show()
            self.ytList.show()
            self.ncmList.show()

            self.newPage_ani_group.stop()

            self.line.show()

            self.__title_ani.setEndValue(QPoint(20, 10))

            self.line_ani.setEndValue(QRect(10, 10 + self.__title.height() + 10, self.width() - 20, 2))

            self.ncmIcon_ani.setEndValue(QPoint(20 + self.__title.width() + 10, 10))

            self.ytIcon_ani.setEndValue(QPoint(20 + self.__title.width() + 10 + 10 + self.ncmIcon.width(), 10))

            self.chooseIcon_ani.setEndValue(QPoint(20 + self.__title.width() + 0, 0))

            self.newPage_ani_group.start()
            return
        
        if self.page == "ncm":
            self.ncmList_ani.stop()
            self.ncmList_ani.setEndValue(QPoint(10, self.height()))
            self.ncmList_ani.start()

        elif self.page == "yt":
            self.ytList_ani.stop()
            self.ytList_ani.setEndValue(QPoint(10, self.height()))
            self.ytList_ani.start()
        

    def loadingAniFinish(self, yt, ncm):
        self.yt = yt
        self.ncm = ncm
        self.updateList()

    def addSongBtn_Clicked(self, _id, _type):
        self.addBtn_OnClicked.emit(_id, _type)

    def insertSongBtn_Clicked(self, _id, _type):
        self.insertBtn_OnClicked.emit(_id, _type)

    def addFavoriteBtn_Clicked(self, _id, _type):
        self.favoriteBtn_OnClicked.emit(_id, _type)

    def updateList(self):

        self.ncmList.init()
        self.ytList.init()
        self.addncmItem()
        self.addytItem()

        self.showListTimer = QTimer()
        self.showListTimer.timeout.connect(self.listReady)
        self.showListTimer.start(100)

    def listReady(self):
        if self.ncmReady and self.ytReady:
            self.showListTimer.stop()
            self.loading.stopAni()
            self.showList()
            if len(self.ncm) > 0 and len(self.yt) > 0:
                return
            p = "ncm"
            if len(self.ncm) == 0:
                p = "yt"
            self.pageAni(p)

    def addncmItem(self):
        if len(self.ncm) > 0:
            self.j = 0
            self.ncmReady = False
            self.ncmTimer = QTimer()
            self.ncmTimer.timeout.connect(self._addncmItem)
            self.ncmTimer.start(10)
        else:
            self.ncmReady = True

    def _addncmItem(self):
        if self.j >= len(self.ncm):
            self.ncmTimer.stop()
            self.ncmReady = True
            return
        data = self.ncm[self.j]
        item = SongItem()
        item._id = str(data["id"])
        item._type = data["type"]
        item.resize(self.width(), 126)
        self.__getImg(item, data)

        item.setTitle(f"{data['artis']} - {data['title']}")
        dt = data["dt"] // 1000
        s = dt
        m = 0
        if dt > 60:
            s = dt % 60
            m = dt // 60

        item.setDt(f"{str(m).zfill(2)}:{str(s).zfill(2)}")
        item.adj()
        item.addBtn_OnClicked.connect(self.addSongBtn_Clicked)
        item.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        item.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)
        
        self.ncmList.addWidget(item, _id=data["id"])
        self.j += 1

    def addytItem(self):
        if len(self.yt) > 0:
            self.i = 0
            self.ytReady = False
            self.yttimer = QTimer()
            self.yttimer.timeout.connect(self._addytItem)
            self.yttimer.start(10)
        else:
            self.ytReady = True

    def _addytItem(self):
        if self.i >= len(self.yt):
            self.yttimer.stop()
            self.ytReady = True
            return
        data = self.yt[self.i]
        item = SongItem()
        item._id = str(data["id"])
        item._type = data["type"]
        item.resize(self.width(), 126)
        self.__getImg(item, data)

        item.setTitle(f"{data['artis']} - {data['title']}")
        dt = data["dt"] // 1000
        s = dt
        m = 0
        if dt > 60:
            s = dt % 60
            m = dt // 60

        item.setDt(f"{str(m).zfill(2)}:{str(s).zfill(2)}")
        item.adj()
        item.addBtn_OnClicked.connect(self.addSongBtn_Clicked)
        item.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        item.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)

        self.ytList.addWidget(item, _id=data["id"])
        self.i += 1

    def __getImg(self, item, i):

        getImg = GetImg(i["img"])
        getImg.finished.connect(lambda: setImg(getImg))
        getImg.start()

        def setImg(t):
            item.setImg(t.data)
            t.data = None
            t.deleteLater()


    def showList(self):
        if self.page == "ncm":
            self.ncmList_ani.stop()
            self.ncmList_ani.setEndValue(QPoint(10, 10 + self.__title.height() + 10 + 10))
            self.ncmList_ani.start()
            self.ytList.move(self.width(), 10 + self.__title.height() + 10 + 10)
        elif self.page == "yt":
            self.ytList_ani.stop()
            self.ytList_ani.setEndValue(QPoint(10, 10 + self.__title.height() + 10 + 10))
            self.ytList_ani.start()
            self.ncmList.move(-self.width(), 10 + self.__title.height() + 10 + 10)


class FavoriteList(QFrame):
    addBtn_OnClicked = Signal(dict)
    insertBtn_OnClicked = Signal(dict)
    updateFavorite = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.page = "close"
        self.favorites = []

        self.hide()

        self.bg = QFrame(self)
        self.bg.setStyleSheet("background: white; border-radius: 25px;")

        self.mainList = SAWidget(self)
        self.list = SAWidget(self)

        self.backBtn = QPushButton(self)
        self.backBtn.setFont(QFont(fontName, 15))
        self.backBtn.setText("回上頁")
        self.backBtn.clicked.connect(self.listCloseAni)
        self.backBtn.adjustSize()

        self.delAllBtn = QPushButton(self)
        self.delAllBtn.setFont(QFont(fontName, 15))
        self.delAllBtn.setText("刪除全部")
        self.delAllBtn.clicked.connect(self.delAllSongs)
        self.delAllBtn.adjustSize()

        self.mainList_ani = QPropertyAnimation(self.mainList, b"pos")
        self.mainList_ani.setDuration(500)
        self.mainList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.list_ani = QPropertyAnimation(self.list, b"pos")
        self.list_ani.setDuration(500)
        self.list_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.backBtn_ani = QPropertyAnimation(self.backBtn, b"pos")
        self.backBtn_ani.setDuration(500)
        self.backBtn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.delAllBtn_ani = QPropertyAnimation(self.delAllBtn, b"pos")
        self.delAllBtn_ani.setDuration(500)
        self.delAllBtn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ani_group = QParallelAnimationGroup(self)
        self.ani_group.addAnimation(self.mainList_ani)
        self.ani_group.addAnimation(self.list_ani)
        self.ani_group.addAnimation(self.backBtn_ani)
        self.ani_group.addAnimation(self.delAllBtn_ani)


    def adj(self):
        mainList_w = self.width() - 20
        mainList_h = self.height() - 6
        mainList_x = -self.width()
        mainList_y = 3

        list_w = self.width() - 20
        list_h = self.height() - self.backBtn.height() - 9
        list_x = self.width()
        list_y = self.backBtn.height() + 6

        backBtn_x = 15 + self.width()
        backBtn_y = 3

        delAllBtn_x = self.backBtn.width() + 20 + self.width()
        delAllBtn_y = 3

        if self.page == "main":
            mainList_x = round((self.width() - mainList_w) / 2)
        elif self.page == "list":
            backBtn_x = 15
            delAllBtn_x = self.backBtn.width() + 20
            list_x = round((self.width() - list_w) / 2)

        self.backBtn.move(backBtn_x, backBtn_y)
        self.delAllBtn.move(delAllBtn_x, delAllBtn_y)

        self.mainList.setGeometry(mainList_x, mainList_y, mainList_w, mainList_h)
        self.list.setGeometry(list_x, list_y, list_w, list_h)
        self.bg.resize(self.width(), self.height())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()

    def init(self, data):
        self.adj()
        self.mainList.initForAddFavorites()
        self.favorites = data
        for i in data:
            self.addMainList(i["title"], i["img"])

    def mainListShowAni(self):
        self.ani_group.stop()
        self.page = "main"
        self.mainList.show()
        self.mainList_ani.setEndValue(QPoint(round((self.width() - self.mainList.width()) / 2), 3))
        self.list_ani.setEndValue(QPoint(self.width(), self.backBtn.height() + 6))
        self.backBtn_ani.setEndValue(QPoint(self.width() + 15, 3))
        self.delAllBtn_ani.setEndValue(QPoint(self.backBtn.width() + 20 + self.width(), 3))

        self.ani_group.start()

    def addMainList(self, title, image):
        item = ListItem()

        item.resize(self.width(), 70)

        item.setTitle(title)
        item.clicked.connect(self.itemClicked)

        item.adj()

        self.mainList.addWidget(item, _id=title)  

        getImg = GetImg(image)
        getImg.finished.connect(lambda: setImg(getImg))
        getImg.start()


        def setImg(t):
            item.setImg(t.data)
            t.data = None
            t.deleteLater()

    def itemClicked(self, title):
        data = [i for i in self.favorites if i["title"] == title][0]

        self.nowData = data
        self.n = 0
        self.list.initForFavorites()
        for i in data["data"]:
            self.addWidget(i)
            self.n += 1
        self.listShowAni()


    def listShowAni(self):
        self.ani_group.stop()
        self.page = "list"
        self.list.show()
        self.mainList_ani.setEndValue(QPoint(-self.width(), 3))
        self.list_ani.setEndValue(QPoint(round((self.width() - self.mainList.width()) / 2), self.backBtn.height() + 6))
        self.backBtn_ani.setEndValue(QPoint(15, 3))
        self.delAllBtn_ani.setEndValue(QPoint(self.backBtn.width() + 20, 3))

        self.ani_group.start()

    def listCloseAni(self):
        self.ani_group.stop()
        self.page = "main"
        self.mainList_ani.setEndValue(QPoint(round((self.width() - self.mainList.width()) / 2), 3))
        self.list_ani.setEndValue(QPoint(self.width(), self.backBtn.height() + 6))
        self.backBtn_ani.setEndValue(QPoint(self.width() + 15, 3))
        self.delAllBtn_ani.setEndValue(QPoint(self.width() + self.backBtn.width() + 20, 3))

        self.ani_group.start()


    def addWidget(self, data):
        item = Favorites_SongItem()
        item._id = str(data["id"])
        item._type = data["type"]
        item._title = self.nowData["title"]
        item.n = self.n
        item.resize(self.width(), 126)

        item.setTitle(f"{data['artis']} - {data['title']}")
        dt = data["dt"] // 1000
        s = dt
        m = 0
        if dt > 60:
            s = dt % 60
            m = dt // 60

        item.setDt(f"{str(m).zfill(2)}:{str(s).zfill(2)}")
        item.adj()
        item.addSongBtn_OnClicked.connect(self.addSongBtn_Clicked)
        item.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        item.delBtn_OnClicked.connect(self.delSongBtn_Clicked)

        self.list.show()
        self.list.addWidget(item, _id=str(data["id"]))

        getImg = GetImg(data["img"])
        getImg.finished.connect(lambda: setImg(getImg))
        getImg.start()


        def setImg(t):
            item.setImg(t.data)
            t.data = None
            t.deleteLater()

    def delAllSongs(self):
        if self.nowData in self.favorites:
            index = self.favorites.index(self.nowData)
            del self.favorites[index]
            self.updateFavorite.emit(self.favorites)
            self.listCloseAni()

    def delSongBtn_Clicked(self, _id, n):
        if self.nowData in self.favorites:
            index = self.favorites.index(self.nowData)
            data = [i for i in self.favorites[index]["data"] if i["id"] == _id][0]
            song_index = self.favorites[index]["data"].index(data)
            del self.favorites[index]["data"][song_index]

            if len(self.favorites[index]["data"]) == 0:
                del self.favorites[index]
                self.updateFavorite.emit(self.favorites)
                self.listCloseAni()
            else:
                self.favorites[index]["img"] = self.favorites[index]["data"][0]["img"]
                self.nowData = self.favorites[index]
                self.list.delSong(n)
                self.updateFavorite.emit(self.favorites)

    
    def addSongBtn_Clicked(self, _id):
        data = [i for i in self.nowData["data"] if i["id"] == _id]
        self.addBtn_OnClicked.emit(data[0])

    def insertSongBtn_Clicked(self, _id):
        data = [i for i in self.nowData["data"] if i["id"] == _id]
        self.insertBtn_OnClicked.emit(data[0])

class AddNewList(QWidget):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.disabled = False

        self.icon_pix = QPixmap("./img/add_icon.png")

        self.enter = QFrame(self)
        self.enter.setStyleSheet("background: rgba(200, 200, 200, 0.3); border-radius: 10px;")
        self.enter.resize(self.size())
        self.enter.hide()

        self.press = QFrame(self)
        self.press.setStyleSheet("background: rgba(200, 200, 200, 0.3); border-radius: 10px;")
        self.press.resize(self.size())
        self.press.hide()


        self.icon = QLabel(self)
        self.icon.setPixmap(self.icon_pix.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation))
        self.icon.setStyleSheet("background: transparent;")
        self.icon.adjustSize()

        self.title = QLabel("新建歌單", self)
        self.title.setFont(QFont(fontName, 15)) 
        self.title.setStyleSheet("background: transparent;")
        self.title.adjustSize()
        

    def adj(self):
        self.icon.setPixmap(self.icon_pix.scaledToHeight(self.height() - 10, Qt.TransformationMode.SmoothTransformation))
        self.icon.adjustSize()

        self.enter.resize(self.size())
        self.press.resize(self.size())

        self.title.resize(self.width() - (5 + self.icon.width() + 5 + 5), self.height() - 10)

        self.icon.move(5, 5)
        self.title.move(self.icon.width() + 10, round((self.height() - self.title.height()) / 2))        

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.disabled:
            return
        self.press.show()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self.disabled:
            return
        self.disabled = True
        self.enter.hide()
        self.press.hide()
        self.clicked.emit()

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        if self.disabled:
            return
        self.enter.show()

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        if self.disabled:
            return
        self.enter.hide()

class AddFavoriteList_Fullbg(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.clicked.emit()

class AddFavoriteList(QWidget):
    addBtn_OnClicked = Signal(str, int)
    insertBtn_OnClicked = Signal(str, int)
    favoriteBtn_OnClicked = Signal(str, int)
    favorites_data_update = Signal(list)
    toast_show = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.hide()
        self.ani_group = None
        self.page = "main"
        self.closing = False

        self.Fullbg = AddFavoriteList_Fullbg(self)
        self.Fullbg.setStyleSheet("background: black;")
        self.Fullbg.resize(self.size())
        self.Fullbg.hide()
        self.Fullbg.clicked.connect(self.closeAni)

        self.Fullbg_opacity = QGraphicsOpacityEffect()
        self.Fullbg_opacity.setOpacity(0)
        self.Fullbg.setGraphicsEffect(self.Fullbg_opacity)

        self.addFavorite = QWidget(self)
        self.addFavorite.setStyleSheet("background: white; border-radius: 25px;")
        self.addFavorite.resize(400, 600)
        self.addFavorite.hide()

        self.addNew = AddNewList(self.addFavorite)
        self.addNew.clicked.connect(self.addNewAni)

        self.list = SAWidget(self.addFavorite)

        self.le = QLineEdit(self.addFavorite)
        self.le.setFont(QFont(fontName, 15))
        self.le.setStyleSheet("background: rgba(200, 200, 200, 0.5); border-radius: 10px;")
        self.le.setPlaceholderText("請輸入歌單名稱")

        self.back_btn = QPushButton(self.addFavorite)
        self.back_btn.setText("返回")
        self.back_btn.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid rgba(200, 200, 200, 1); border-radius: 15px; } QPushButton:hover { background-color: rgba(0, 0, 0, 0.1); } QPushButton:pressed { background-color: rgba(0, 0, 0, 0.2); }")
        self.back_btn.setFont(QFont(fontName, 15))
        self.back_btn.clicked.connect(self.back_btn_Clicked)

        self.ok_btn = QPushButton(self.addFavorite)
        self.ok_btn.setText("建立")
        self.ok_btn.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid rgba(200, 200, 200, 1); border-radius: 15px; } QPushButton:hover { background-color: rgba(0, 0, 0, 0.1); } QPushButton:pressed { background-color: rgba(0, 0, 0, 0.2); }")
        self.ok_btn.setFont(QFont(fontName, 15))
        self.ok_btn.clicked.connect(self.ok_btn_Clicked)

        self.addFavoritebg_ani = QPropertyAnimation(self.addFavorite, b"geometry")
        self.addFavoritebg_ani.setDuration(750)
        self.addFavoritebg_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.addNew_ani = QPropertyAnimation(self.addNew, b"geometry")
        self.addNew_ani.setDuration(750)
        self.addNew_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.le_ani = QPropertyAnimation(self.le, b"pos")
        self.le_ani.setDuration(750)
        self.le_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.back_btn_ani = QPropertyAnimation(self.back_btn, b"pos")
        self.back_btn_ani.setDuration(750)
        self.back_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.ok_btn_ani = QPropertyAnimation(self.ok_btn, b"pos")
        self.ok_btn_ani.setDuration(750)
        self.ok_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.Fullbg_ani = QPropertyAnimation(self.Fullbg_opacity, b"opacity")
        self.Fullbg_ani.setDuration(750)
        self.Fullbg_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.list_ani = QPropertyAnimation(self.list, b"pos")
        self.list_ani.setDuration(750)
        self.list_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.adj()


    def adj(self):
        if self.page == "main":
            self.addFavorite.resize(400, 600)

        elif self.page == "addNew":
            self.addFavorite.resize(400, 150)


        self.Fullbg.resize(self.size())
        self.list.resize(self.addFavorite.width() - 40, self.addFavorite.height() - 40 - 70)
        self.le.resize(self.addFavorite.width() - 30, 40)
        self.back_btn.resize(100, 30)
        self.ok_btn.resize(100, 30)

        if self.page == "main":
            self.le.move(round((self.addFavorite.width() - self.le.width()) / 2), self.addFavorite.height())
            self.addNew.setGeometry(20, 20, self.addFavorite.width() - 40, 70)
            self.list.move(20, 20 + 70)
            self.addFavorite.setGeometry(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - self.addFavorite.height()) / 2), self.addFavorite.width(), self.addFavorite.height())
            self.back_btn.move(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, self.addFavorite.height())
            self.ok_btn.move(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2), self.addFavorite.height())

        elif self.page == "addNew":
            self.le.move(round((self.addFavorite.width() - self.le.width()) / 2), round((self.addFavorite.height() - self.le.height()) / 2))
            self.addFavorite.setGeometry(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - 150) / 2), self.addFavorite.width(), 150)
            self.list.move(20, self.addFavorite.height())
            self.addNew.setGeometry(10, 10, self.addFavorite.width() - 20, 40)
            self.back_btn.move(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, self.addFavorite.height() - 20 - self.back_btn.height())
            self.ok_btn.move(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2), self.addFavorite.height() - 20 - self.ok_btn.height())

    def ok_btn_Clicked(self):
        if len([i for i in self.favorites if i["title"] == self.le.text()]) != 0:
            self.toast_show.emit("該名稱已被使用", "rgba(255, 50, 50, 1)")
            return
        
        if len(self.le.text()) == 0:
            self.toast_show.emit("至少輸入一個字元", "rgba(255, 50, 50, 1)")
            return
        
        elif len(self.le.text()) >= 30:
            self.toast_show.emit("不得輸入超過30個字元", "rgba(255, 50, 50, 1)")
            return

        self.favorites.insert(0, {
            "title": self.le.text(),
            "img": self.song["img"],
            "data": [self.song]
        })

        self.favorites_data_update.emit(self.favorites)

        self.closeAni()
        self.toast_show.emit("添加成功", "rgba(46, 204, 113, 1)")


    def closeAni(self):
        if self.closing:
            return

        if self.ani_group != None:
            self.ani_group.stop()

        self.closing = True
        self.addFavoritebg_ani.setStartValue(self.addFavorite.geometry())
        self.addFavoritebg_ani.setEndValue(QRect(round((self.width() - self.addFavorite.width()) / 2), self.height(), self.addFavorite.width(), self.addFavorite.height()))

        self.Fullbg_ani.setStartValue(self.Fullbg_opacity.opacity())
        self.Fullbg_ani.setEndValue(0)

        self.ani_group = QParallelAnimationGroup(self)
        self.ani_group.addAnimation(self.addFavoritebg_ani)
        self.ani_group.addAnimation(self.Fullbg_ani)
        self.ani_group.start()
        self.ani_group.finished.connect(self.closeAni2)

    def closeAni2(self):
        self.hide()
        self.page = "main"
        self.adj()

    def back_btn_Clicked(self):
        if self.ani_group != None:
            self.ani_group.stop()
        self.addNew.disabled = False

        self.list_ani.setStartValue(QPoint(20, 150))
        self.list_ani.setEndValue(QPoint(20, 20 + 70))

        self.addFavoritebg_ani.setStartValue(QRect(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - self.addFavorite.height()) / 2), self.addFavorite.width(), 150))
        self.addFavoritebg_ani.setEndValue(QRect(self.addFavorite.pos().x(), round((self.height() - 600) / 2), self.addFavorite.width(), 600))

        self.addNew_ani.setStartValue(QRect(10, 10, self.addFavorite.width() - 20, 40))
        self.addNew_ani.setEndValue(QRect(20, 20, self.addFavorite.width() - 40, 70))

        self.le_ani.setStartValue(QPoint(self.le.pos().x(), round((150 - self.le.height()) / 2)))
        self.le_ani.setEndValue(QPoint(self.le.pos().x(), 600))

        self.back_btn_ani.setStartValue(QPoint(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, 150 - 10 - self.back_btn.height()))
        self.back_btn_ani.setEndValue(QPoint(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, 600))

        self.ok_btn_ani.setStartValue(QPoint(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.ok_btn.width()) / 2), 150 - 10 - self.ok_btn.height()))
        self.ok_btn_ani.setEndValue(QPoint(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.ok_btn.width()) / 2), 600))

        self.ani_group = QParallelAnimationGroup(self)
        self.ani_group.addAnimation(self.addFavoritebg_ani)
        self.ani_group.addAnimation(self.list_ani)
        self.ani_group.addAnimation(self.addNew_ani)
        self.ani_group.addAnimation(self.le_ani)
        self.ani_group.addAnimation(self.back_btn_ani)
        self.ani_group.addAnimation(self.ok_btn_ani)

        self.ani_group.start()
        self.page = "main"

    def openAni(self, song):
        if self.ani_group != None:
            self.ani_group.stop()

        self.init(self.favorites)
        
        self.closing = False
        self.song = song
        self.show()
        self.Fullbg.show()
        self.addFavorite.show()
        self.list.show()
        self.addNew.disabled = False

        self.addFavoritebg_ani.setStartValue(QRect(round((self.width() - self.addFavorite.width()) / 2), self.height(), self.addFavorite.width(), self.addFavorite.height()))
        self.addFavoritebg_ani.setEndValue(QRect(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - self.addFavorite.height()) / 2), self.addFavorite.width(), self.addFavorite.height()))

        self.Fullbg_ani.setStartValue(0)
        self.Fullbg_ani.setEndValue(0.7)

        self.list_ani.setStartValue(QPoint(20, self.addFavorite.height()))
        self.list_ani.setEndValue(QPoint(20, 20 + self.addNew.height()))

        self.addNew_ani.setStartValue(QRect(0, -self.addNew.height(), self.addFavorite.width() - 40, 70))
        self.addNew_ani.setEndValue(QRect(20, 20, self.addFavorite.width() - 40, 70))

        self.ani_group = QParallelAnimationGroup(self)
        self.ani_group.addAnimation(self.addFavoritebg_ani)
        self.ani_group.addAnimation(self.Fullbg_ani)
        self.ani_group.addAnimation(self.list_ani)
        self.ani_group.addAnimation(self.addNew_ani)
        self.ani_group.start()
        self.page = "main"

    def addNewAni(self):
        if self.ani_group != None:
            self.ani_group.stop()
        self.le.setText("")
        self.le.show()
        self.back_btn.show()
        self.ok_btn.show()
        self.list_ani.setStartValue(QPoint(20, 20 + self.addNew.height()))
        self.list_ani.setEndValue(QPoint(20, 150))

        self.addFavoritebg_ani.setStartValue(QRect(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - self.addFavorite.height()) / 2), self.addFavorite.width(), self.addFavorite.height()))
        self.addFavoritebg_ani.setEndValue(QRect(round((self.width() - self.addFavorite.width()) / 2), round((self.height() - 150) / 2), self.addFavorite.width(), 150))

        self.addNew_ani.setStartValue(QRect(20, 20, self.addFavorite.width() - 40, 70))
        self.addNew_ani.setEndValue(QRect(10, 10, self.addFavorite.width() - 20, 40))

        self.le_ani.setStartValue(QPoint(self.le.pos().x(), self.addFavorite.height()))
        self.le_ani.setEndValue(QPoint(self.le.pos().x(), round((150 - self.le.height()) / 2)))

        self.back_btn_ani.setStartValue(QPoint(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, self.addFavorite.height()))
        self.back_btn_ani.setEndValue(QPoint(round(((self.addFavorite.width() / 2) - 20 - self.back_btn.width()) / 2) + 20, 150 - 10 - self.back_btn.height()))

        self.ok_btn_ani.setStartValue(QPoint(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.ok_btn.width()) / 2), self.addFavorite.height()))
        self.ok_btn_ani.setEndValue(QPoint(round(self.addFavorite.width() / 2) + round(((self.addFavorite.width() / 2) - 20 - self.ok_btn.width()) / 2), 150 - 10 - self.ok_btn.height()))

        self.ani_group = QParallelAnimationGroup(self)
        self.ani_group.addAnimation(self.addFavoritebg_ani)
        self.ani_group.addAnimation(self.list_ani)
        self.ani_group.addAnimation(self.addNew_ani)
        self.ani_group.addAnimation(self.le_ani)
        self.ani_group.addAnimation(self.back_btn_ani)
        self.ani_group.addAnimation(self.ok_btn_ani)

        self.ani_group.start()
        self.page = "addNew"


    def init(self, data: list):
        self.favorites = data
        self.list.initForAddFavorites()
        for i in data:
            self.addWidget(i["title"], i["img"])

    def addWidget(self, title, image: str):
        item = ListItem()

        item.resize(self.width(), 70)

        item.setTitle(title)

        item.clicked.connect(self.itemClicked)

        item.adj()
        self.list.addWidget(item, _id=title) 

        if image.startswith("./img/"):
            item._setImg(image)
        else:
            getImg = GetImg(image)
            getImg.finished.connect(lambda: setImg(getImg))
            getImg.start()

            def setImg(t):
                item.setImg(t.data)
                t.data = None
                t.deleteLater()

    def itemClicked(self, title):

        for i in self.favorites:
            if i["title"] == title:
                d = [j for j in i["data"] if j["id"] == self.song["id"]]
                print(d)
                if len(d) > 0:
                    self.toast_show.emit("無法添加重複歌曲", "rgba(255, 50, 50, 1)")
                    return
                i["data"].insert(0, self.song)
                i["img"] = self.song["img"]
                break

        self.favorites_data_update.emit(self.favorites)

        self.closeAni()
        self.toast_show.emit("添加成功", "rgba(46, 204, 113, 1)")


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()

class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]

        self.setFont(QFont(fontName, 20))
    
    def _setText(self, text, color):
        self.setText(f" {text} ")
        self.setStyleSheet(f"background: {color}; border-radius: 5px; color: white;")
        self.adjustSize()

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.bg = QFrame(self)
        self.bg.setStyleSheet("background: white; border-radius: 25px;")

        self.adj()

    def adj(self):
        self.bg.resize(self.size())


    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()


class Window(AcrylicWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        #self.windowEffect.setMicaEffect(self.winId(), True)
        #self.windowEffect.setAeroEffect(self.winId())
        #self.windowEffect.setAcrylicEffect(self.winId(), "106EBE99")
        #self.windowEffect.setAcrylicEffect(self.winId(), "10000000")


        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]
        self.offset = 5
        self.margin = 15

        self.topRim = 50
        self.rim = 20

        self.favorites = self.getFavorites()
        self.playList = []
        self.DownloadList = []
        self.yt = []
        self.ncm = []
        self.np = 0
        self.player_status = "close"
        self.toastShow = False
        self.downloading = False
        self.search = 0
        self.searchBarUP = False
        self.favoriteListShow = False
        self.songListShow = False
        self.playerBtnShow = False
        self.searchListShow = False
        self.settingsPageShow = False

        self.setMinimumSize(1280, 720)

        self.getNCMSong = GetSongList("getncm.exe")
        self.getNCMSong.progress_updated.connect(self.ncmProgress_updated)
        self.getNCMSong.finished.connect(self.ncmDownload_finish)

        self.getYTSong = GetYT()
        self.getYTSong.updateGUI.connect(self.ytProgress_updated)
        self.getYTSong.finished.connect(self.ytDownload_finish)

        self.getYTList = GetSongList("getyt.exe")
        self.getYTList.finished.connect(self.searchYTFinish)

        self.getNCMList = GetSongList("getncm.exe")
        self.getNCMList.finished.connect(self.searchNCMFinish)

        self.player = Player()
        self.player.opt.connect(self.player_output)
        self.player.sendSongData_opt.connect(self.sendSong_opt)

        self.player.finished.connect(self.player_close)

        self.settingsBtn_Shadow = QFrame(self)
        self.settingsBtn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.settingsBtn_Shadow.resize(50, 50)

        self.settingsBtn = SettingsButton(self)
        self.settingsBtn.clicked.connect(self.settingsBtnClicked)
        #self.settingsBtn_IAni = IconAni("./img/setting_icon.png", self)

        self.play_pause_btn_Shadow = QFrame(self)
        self.play_pause_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.play_pause_btn_Shadow.resize(50, 50)

        self.play_pause_btn = Play_Pause_Button(self)
        self.play_pause_btn.setPlayer(self.player)
        #self.play_pause_btn_IAni = IconAni("./img/pause_icon.png", self)


        self.skip_btn_Shadow = QFrame(self)
        self.skip_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.skip_btn_Shadow.resize(50, 50)

        self.skip_btn = Skip_Button(self)
        self.skip_btn.clicked.connect(self.skip_btn_onClicked)

        #self.skip_btn_IAni = IconAni("./img/skip_icon.png", self)

        self.reload_btn_Shadow = QFrame(self)
        self.reload_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.reload_btn_Shadow.resize(50, 50)

        self.reload_btn = Reload_Button(self)
        self.reload_btn.setPlayer(self.player)
        #self.reload_btn_IAni = IconAni("./img/reload_icon.png", self)


        self.favorite_btn_Shadow = QFrame(self)
        self.favorite_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.favorite_btn_Shadow.resize(50, 50)

        self.favorite_btn = Favorite_Button(self)
        self.favorite_btn.clicked.connect(self.favoriteBtnClicked)
        #self.favorite_btn_IAni = IconAni("./img/favorite_icon.png", self)

        self.songList_btn_Shadow = QFrame(self)
        self.songList_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.songList_btn_Shadow.resize(50, 50)

        self.songList_btn = SongListButton(self)
        self.songList_btn.clicked.connect(self.songListBtnClicked)

        self.search_btn_Shadow = QFrame(self)
        self.search_btn_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.search_btn_Shadow.resize(50, 50)

        self.search_btn = SearchButton(self)
        self.search_btn.clicked.connect(self.le_returnPressed)
        #self.search_btn_IAni = IconAni("./img/search_icon.png", self)

        self.searchBar_bg_Shadow = QFrame(self)
        self.searchBar_bg_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.searchBar_bg_Shadow.setMinimumSize(700, 50)

        self.searchBar_bg = QFrame(self)
        self.searchBar_bg.setMinimumSize(700, 50)
        self.searchBar_bg.setStyleSheet("background: white; border-radius: 25px;")

        self.le = QLineEdit(self)
        self.le.setMinimumSize(650, 38)
        self.le.setFont(QFont(fontName, 20))
        self.le.setPlaceholderText("請在此搜尋歌曲")
        self.le.setStyleSheet("border-radius: 10px;")
        self.le.returnPressed.connect(self.le_returnPressed)

        self.searchListBg_Shadow = QFrame(self)
        self.searchListBg_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.searchListBg_Shadow.hide()

        self.searchListBg = QFrame(self)
        self.searchListBg.setStyleSheet("background: white; border-radius: 25px;")
        self.searchListBg.hide()

        self.searchList = SearchList(self)
        self.searchList.addBtn_OnClicked.connect(self.addSongBtn_Clicked)
        self.searchList.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        self.searchList.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)

        self.songListBg_Shadow = QFrame(self)
        self.songListBg_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")
        self.songListBg_Shadow.hide()

        self.songListBg = QFrame(self)
        self.songListBg.setStyleSheet("background: white; border-radius: 25px;")
        self.songListBg.hide()

        self.songList = SongList(self)
        self.songList.delSongBtn_OnClicked.connect(self.delSongBtn_Clicked)
        self.songList.insertBtn_OnClicked.connect(self.insertSongBtn_Clicked)
        self.songList.favoriteBtn_OnClicked.connect(self.addFavoriteBtn_Clicked)

        self.favoriteList_Shadow = QFrame(self)
        self.favoriteList_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")

        self.favoriteList = FavoriteList(self)
        self.favoriteList.updateFavorite.connect(self.favoritesDataUpdate)
        self.favoriteList.addBtn_OnClicked.connect(self.addSong_fv)
        self.favoriteList.insertBtn_OnClicked.connect(self.insertSong_fv)

        self.addFavoriteList = AddFavoriteList(self)
        self.addFavoriteList.init(self.favorites)
        self.addFavoriteList.favorites_data_update.connect(self.favoritesDataUpdate)
        self.addFavoriteList.toast_show.connect(self.toastShowAni)


        self.settingsPage_Shadow = QFrame(self)
        self.settingsPage_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 25px;")

        self.settingsPage = SettingsPage(self)

        
        self.toastBg_Shadow = QFrame(self)
        self.toastBg_Shadow.setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 5px;")

        self.toast = Toast(self)

        self.titleBar.raise_()

##

        self.settingsPage_Shadow_ani = QPropertyAnimation(self.settingsPage_Shadow, b"pos")
        self.settingsPage_Shadow_ani.setDuration(750)
        self.settingsPage_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.settingsPage_ani = QPropertyAnimation(self.settingsPage, b"pos")
        self.settingsPage_ani.setDuration(750)
        self.settingsPage_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.favoriteList_ani = QPropertyAnimation(self.favoriteList, b"geometry")
        self.favoriteList_ani.setDuration(750)
        self.favoriteList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.favoriteList_Shadow_ani = QPropertyAnimation(self.favoriteList_Shadow, b"geometry")
        self.favoriteList_Shadow_ani.setDuration(750)
        self.favoriteList_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.toast_ani = QPropertyAnimation(self.toast, b"pos")
        self.toast_ani.setDuration(750)
        self.toast_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.toastBg_Shadow_ani = QPropertyAnimation(self.toastBg_Shadow, b"pos")
        self.toastBg_Shadow_ani.setDuration(750)
        self.toastBg_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchList_ani = QPropertyAnimation(self.searchList, b"geometry")
        self.searchList_ani.setDuration(750)
        self.searchList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchListBg_ani = QPropertyAnimation(self.searchListBg, b"geometry")
        self.searchListBg_ani.setDuration(750)
        self.searchListBg_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchListBg_Shadow_ani = QPropertyAnimation(self.searchListBg_Shadow, b"geometry")
        self.searchListBg_Shadow_ani.setDuration(750)
        self.searchListBg_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.songListBg_Shadow_ani = QPropertyAnimation(self.songListBg_Shadow, b"pos")
        self.songListBg_Shadow_ani.setDuration(750)
        self.songListBg_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.songListBg_ani = QPropertyAnimation(self.songListBg, b"pos")
        self.songListBg_ani.setDuration(750)
        self.songListBg_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.songList_ani = QPropertyAnimation(self.songList, b"pos")
        self.songList_ani.setDuration(750)
        self.songList_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.play_pause_btn_Shadow_ani = QPropertyAnimation(self.play_pause_btn_Shadow, b"pos")
        self.play_pause_btn_Shadow_ani.setDuration(750)
        self.play_pause_btn_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.play_pause_btn_ani = QPropertyAnimation(self.play_pause_btn, b"pos")
        self.play_pause_btn_ani.setDuration(750)
        self.play_pause_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.skip_btn_Shadow_ani = QPropertyAnimation(self.skip_btn_Shadow, b"pos")
        self.skip_btn_Shadow_ani.setDuration(750)
        self.skip_btn_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.skip_btn_ani = QPropertyAnimation(self.skip_btn, b"pos")
        self.skip_btn_ani.setDuration(750)
        self.skip_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.reload_btn_Shadow_ani = QPropertyAnimation(self.reload_btn_Shadow, b"pos")
        self.reload_btn_Shadow_ani.setDuration(750)
        self.reload_btn_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.reload_btn_ani = QPropertyAnimation(self.reload_btn, b"pos")
        self.reload_btn_ani.setDuration(750)
        self.reload_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.search_btn_Shadow_ani = QPropertyAnimation(self.search_btn_Shadow, b"pos")
        self.search_btn_Shadow_ani.setDuration(750)
        self.search_btn_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.search_btn_ani = QPropertyAnimation(self.search_btn, b"pos")
        self.search_btn_ani.setDuration(750)
        self.search_btn_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchBar_bg_Shadow_ani = QPropertyAnimation(self.searchBar_bg_Shadow, b"geometry")
        self.searchBar_bg_Shadow_ani.setDuration(750)
        self.searchBar_bg_Shadow_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchBar_bg_ani = QPropertyAnimation(self.searchBar_bg, b"geometry")
        self.searchBar_bg_ani.setDuration(750)
        self.searchBar_bg_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.le_ani = QPropertyAnimation(self.le, b"geometry")
        self.le_ani.setDuration(750)
        self.le_ani.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.searchBar_ani_group = QParallelAnimationGroup(self)
        self.searchBar_ani_group.addAnimation(self.searchBar_bg_ani)
        self.searchBar_ani_group.addAnimation(self.searchBar_bg_Shadow_ani)
        self.searchBar_ani_group.addAnimation(self.le_ani)
        self.searchBar_ani_group.addAnimation(self.search_btn_ani)
        self.searchBar_ani_group.addAnimation(self.search_btn_Shadow_ani)

        self.searchList_ani_group = QParallelAnimationGroup(self)
        self.searchList_ani_group.addAnimation(self.searchList_ani)
        self.searchList_ani_group.addAnimation(self.searchListBg_ani)
        self.searchList_ani_group.addAnimation(self.searchListBg_Shadow_ani)

        self.favorite_ani_group = QParallelAnimationGroup(self)
        self.favorite_ani_group.addAnimation(self.favoriteList_ani)
        self.favorite_ani_group.addAnimation(self.favoriteList_Shadow_ani)

        self.SongList_ani_group = QParallelAnimationGroup(self)
        self.SongList_ani_group.addAnimation(self.songList_ani)
        self.SongList_ani_group.addAnimation(self.songListBg_ani)
        self.SongList_ani_group.addAnimation(self.songListBg_Shadow_ani)

        self.playerBtn_ani_group = QParallelAnimationGroup(self)
        self.playerBtn_ani_group.addAnimation(self.play_pause_btn_Shadow_ani)
        self.playerBtn_ani_group.addAnimation(self.play_pause_btn_ani)
        self.playerBtn_ani_group.addAnimation(self.skip_btn_Shadow_ani)
        self.playerBtn_ani_group.addAnimation(self.skip_btn_ani)
        self.playerBtn_ani_group.addAnimation(self.reload_btn_Shadow_ani)
        self.playerBtn_ani_group.addAnimation(self.reload_btn_ani)

        self.settingsPage_ani_group = QParallelAnimationGroup(self)
        self.settingsPage_ani_group.addAnimation(self.settingsPage_Shadow_ani)
        self.settingsPage_ani_group.addAnimation(self.settingsPage_ani)


##

        self.toastTimer = QTimer(self)
        self.toastTimer.setSingleShot(True)

        self.adj()

        self.favoriteList.init(self.favorites)
    
    def toastShowAni(self, text, color):
        if self.toastShow:
            self.toastColseAni(True, text, color)
            return

        self.toast._setText(text, color)
        self.toastBg_Shadow.resize(self.toast.size())
        self.toastShow = True
        x = round((self.width() - self.toast.width()) / 2)
        st_y = -self.toast.height() - 10
        ed_y = self.topRim
        self.toast_ani.setStartValue(QPoint(x, st_y))
        self.toast_ani.setEndValue(QPoint(x, ed_y))

        self.toastBg_Shadow_ani.setStartValue(QPoint(x + self.offset, st_y + self.offset))
        self.toastBg_Shadow_ani.setEndValue(QPoint(x + self.offset, ed_y + self.offset))

        self.toast_ani_group = QParallelAnimationGroup(self)
        self.toast_ani_group.addAnimation(self.toast_ani)
        self.toast_ani_group.addAnimation(self.toastBg_Shadow_ani)
        self.toast_ani_group.start()
        self.toast_ani_group.finished.connect(self.toastShowAni2)

    def toastShowAni2(self):
        self.toastTimer.start(2500)
        self.toastTimer.timeout.connect(self.toastColseAni)

    def toastColseAni(self, re=False, text="None", color="None"):
        self.toast_ani_group.stop()
        self.toastTimer.stop()
        x = round((self.width() - self.toast.width()) / 2)
        st_y = self.topRim
        ed_y = -self.toast.height() - 10
        self.toast_ani.setStartValue(QPoint(self.toast.pos()))
        self.toast_ani.setEndValue(QPoint(x, ed_y))

        self.toastBg_Shadow_ani.setStartValue(QPoint(self.toastBg_Shadow.pos()))
        self.toastBg_Shadow_ani.setEndValue(QPoint(x + self.offset, ed_y + self.offset))

        self.toast_ani_group = QParallelAnimationGroup(self)
        self.toast_ani_group.addAnimation(self.toast_ani)
        self.toast_ani_group.addAnimation(self.toastBg_Shadow_ani)
        self.toast_ani_group.start()

        self.toast_ani_group.finished.connect(lambda: self.toastColseAni2(re, text, color))

    def toastColseAni2(self, re=False, text="None", color="None"):
        self.toastShow = False
        if re:
            self.toastShowAni(text, color)


    def favoritesDataUpdate(self, data):
        self.favorites = data
        with open("./favorites.json", 'w', encoding='utf-8') as file:
            json.dump(self.favorites, file, ensure_ascii=False, indent=4)

        self.addFavoriteList.init(self.favorites)
        self.favoriteList.init(self.favorites)

    def getFavorites(self):
        if os.path.exists("./favorites.json"):
            with open("./favorites.json", 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data
        else:
            with open("./favorites.json", 'w', encoding='utf-8') as file:
                json.dump([], file)
            return []
        
    def delSongBtn_Clicked(self, g):
        del self.playList[g]

    def skip_btn_onClicked(self):
        if self.np + 1 >= len(self.playList):
            #self.songList.setAlreadyPlay(self.np)
            #self.player_status = "standby"
            return
        self.np += 1
        song = self.playList[self.np]
        path = "ncm"
        if song["type"] == 1:
            path = "yt"
        if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):
            self.player.sendSongData(song, "ok")
        else:
            t = QTimer()
            t.timeout.connect(lambda: checkFile(self, path, song, t))
            t.start(100)
            
            def checkFile(self, path, song, t):
                if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):
                    self.player.sendSongData(song, "ok")
                    t.stop()
                    t.deleteLater()

    def adj(self):

        toast_x = round((self.width() - self.toast.width()) / 2)
        toast_y = -self.toast.height() - 10
        
        if self.toastShow:
            toast_y = self.topRim

        self.toast.move(toast_x, toast_y)
        self.toastBg_Shadow.move(toast_x + self.offset, toast_y + self.offset)

        searchBtn_x = round((self.width() - self.searchBar_bg.width()) / 2) + self.searchBar_bg.width() + self.margin
        searchBtn_y = round((self.height() - self.searchBar_bg.height()) / 2)

        le_w = 650
        le_h = 38
        le_x = round((self.width() - le_w) / 2)
        le_y = round((self.height() - le_h) / 2)

        searchBg_w = 700
        searchBg_h = 50
        searchBg_x = round((self.width() - searchBg_w) / 2)
        searchBg_y = round((self.height() - searchBg_h) / 2)

        searchList_w = self.width() - self.rim * 2
        searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        searchList_x = self.rim
        searchList_y = self.height()

        songList_w = round(self.width() / 2) - self.rim - 10
        songList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        songList_x = self.width()
        songList_y = self.topRim + self.searchBar_bg.height() + self.margin

        playPauseBtn_x = self.rim
        playPauseBtn_y = self.height()

        skipBtn_x = self.rim + self.margin + self.play_pause_btn.width()
        skipBtn_y = self.height()

        reloadBtn_x = self.rim + self.play_pause_btn.width() + self.skip_btn.width() + self.margin * 2
        reloadBtn_y = self.height()

        favoriteList_w = round(self.width() / 2) - self.rim - 10
        favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        favoriteList_x = -favoriteList_w - self.offset
        favoriteList_y = self.topRim + self.searchBar_bg.height() + self.margin

        if self.searchBarUP:
            searchBtn_x = self.width() - (self.settingsBtn.width() + self.songList_btn.width() + self.search_btn.width() + self.margin * 2 + self.rim)
            searchBtn_y = self.topRim

            le_w = self.width() - (self.favorite_btn.width() + self.search_btn.width() + self.songList_btn.width() + self.settingsBtn.width() + self.rim * 2 + self.margin * 4) - 50
            le_h = self.le.height()
            le_x = self.rim + self.favorite_btn.width() + self.margin + 25
            le_y = self.topRim + round((self.searchBar_bg.height() - self.le.height()) / 2)

            searchBg_w = self.width() - (self.favorite_btn.width() + self.search_btn.width() + self.songList_btn.width() + self.settingsBtn.width() + self.rim * 2 + self.margin * 4)
            searchBg_h = self.searchBar_bg.height()
            searchBg_x = self.rim + self.favorite_btn.width() + self.margin
            searchBg_y = self.topRim

        if self.searchListShow:
            searchList_y = self.topRim + self.searchBar_bg.height() + self.margin

        if self.songListShow:
            searchList_w = songList_w
            songList_x = round(self.width() / 2) + 10

        if self.playerBtnShow:
            searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.play_pause_btn.height() + self.margin * 2 + self.rim)
            playPauseBtn_y = self.topRim + self.searchBar_bg.height() + searchList_h + self.margin * 2
            skipBtn_y = playPauseBtn_y
            reloadBtn_y = playPauseBtn_y
            favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.play_pause_btn.height() + self.margin * 2 + self.rim)


        self.search_btn.move(searchBtn_x, searchBtn_y)
        self.search_btn_Shadow.move(searchBtn_x + self.offset, searchBtn_y + self.offset)

        self.le.setGeometry(le_x, le_y, le_w, le_h)

        self.searchBar_bg.setGeometry(searchBg_x, searchBg_y, searchBg_w, searchBg_h)
        self.searchBar_bg_Shadow.setGeometry(searchBg_x + self.offset, searchBg_y + self.offset, searchBg_w, searchBg_h)

        self.searchList.setGeometry(searchList_x, searchList_y, searchList_w, searchList_h)
        self.searchListBg.setGeometry(searchList_x, searchList_y, searchList_w, searchList_h)
        self.searchListBg_Shadow.setGeometry(searchList_x + self.offset, searchList_y + self.offset, searchList_w, searchList_h)

        self.songList.setGeometry(songList_x, songList_y, songList_w, songList_h)
        self.songListBg.setGeometry(songList_x, songList_y, songList_w, songList_h)
        self.songListBg_Shadow.setGeometry(songList_x + self.offset, songList_y + self.offset, songList_w, songList_h)

        self.play_pause_btn.move(playPauseBtn_x, playPauseBtn_y)
        self.play_pause_btn_Shadow.move(playPauseBtn_x + self.offset, playPauseBtn_y + self.offset)

        self.skip_btn.move(skipBtn_x, skipBtn_y)
        self.skip_btn_Shadow.move(skipBtn_x + self.offset, skipBtn_y + self.offset)

        self.reload_btn.move(reloadBtn_x, reloadBtn_y)
        self.reload_btn_Shadow.move(reloadBtn_x + self.offset, reloadBtn_y + self.offset)


        if self.favoriteListShow:
            favoriteList_x = self.rim

        self.favoriteList.setGeometry(favoriteList_x, favoriteList_y, favoriteList_w, favoriteList_h)
        self.favoriteList_Shadow.setGeometry(favoriteList_x + self.offset, favoriteList_y + self.offset, favoriteList_w, favoriteList_h)


        favoriteBtn_x = self.rim
        favoriteBtn_y = self.topRim

        settingsBtn_x = self.width() - self.settingsBtn.width() - self.rim
        settingsBtn_y = self.topRim

        songListBtn_x = self.width() - (self.settingsBtn.width() + self.rim + self.margin + self.songList_btn.width())
        songListBtn_y = self.topRim

        self.favorite_btn.move(favoriteBtn_x, favoriteBtn_y)
        self.favorite_btn_Shadow.move(favoriteBtn_x + self.offset, favoriteBtn_y + self.offset)

        self.songList_btn.move(songListBtn_x, songListBtn_y)
        self.songList_btn_Shadow.move(songListBtn_x + self.offset, songListBtn_y + self.offset)

        self.settingsBtn.move(settingsBtn_x, settingsBtn_y)
        self.settingsBtn_Shadow.move(settingsBtn_x + self.offset, settingsBtn_y + self.offset)

        settingsPage_w = self.width() - self.rim * 2
        settingsPage_h = self.height() - (self.topRim + self.rim)
        settingsPage_x = self.rim
        settingsPage_y = -settingsPage_h - self.offset

        if self.settingsPageShow:
            settingsPage_y = self.topRim

        self.settingsPage.setGeometry(settingsPage_x, settingsPage_y, settingsPage_w, settingsPage_h)
        self.settingsPage_Shadow.setGeometry(settingsPage_x + self.offset, settingsPage_y + self.offset, settingsPage_w, settingsPage_h)

        self.addFavoriteList.setGeometry(0, 0, self.width(), self.height())

    def sendSong_opt(self, status):
        if status == "ok":
            self.player_status = "play"
            self.songList.setPlay(self.np)
    
    def nextSong(self):
        if self.np + 1 >= len(self.playList):
            self.songList.setAlreadyPlay(self.np)
            self.player_status = "standby"
            return
        self.np += 1
        song = self.playList[self.np]
        path = "ncm"
        if song["type"] == 1:
            path = "yt"
        if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):
            self.player.sendSongData(song, "ok")
        else:
            t = QTimer()
            t.timeout.connect(lambda: checkFile(self, path, song, t))
            t.start(100)
            
            def checkFile(self, path, song, t):
                if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):
                    self.player.sendSongData(song, "ok")
                    t.stop()
                    t.deleteLater()


    def player_output(self, opt):
        if opt == "finish":
            song = self.playList[self.np]
            path = "ncm"
            if song["type"] == 1:
                path = "yt"
            if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):

                self.player.sendSongData(song, "ok")
        elif opt == "next_song":
            self.nextSong()

    def player_start(self):
        if self.player_status == "close":
            self.player_status = "standby"
            self.playerBtnShowAni()
            self.player.start()
        elif self.player_status == "standby":
            self.np += 1
            song = self.playList[self.np]
            path = "ncm"
            if song["type"] == 1:
                path = "yt"
            if os.path.isfile(f"./cache/{path}/{song['id']}.mp3"):
                self.player.sendSongData(song, "ok")

    def player_close(self):
        self.playerBtnCloseAni()
        self.songList.setAlreadyPlay(self.np)
        self.np += 1
        self.play_pause_btn.init()
        self.player_status = "close"

    def addSong_fv(self, data):
        if data not in self.DownloadList:
            self.DownloadList.append(data)

        if not self.downloading:
            self.downloading = True
            self.downloadSong()

        self.playList.append(data)

        if not self.songListShow:
            self.songListShowAni()
        
        self.songList.addList(data)

    def insertSong_fv(self, data):
        if data not in self.DownloadList:
            self.DownloadList.append(data)

        if not self.downloading:
            self.downloading = True
            self.downloadSong()

        self.playList.insert(self.np + 1, data)

        if not self.songListShow:
            self.songListShowAni()

        self.songList.insertList(data, self.np)

    def addSongBtn_Clicked(self, _id, _type):
        if _type == 0:
            song = [i for i in self.ncm if str(i['id']) == _id]
            if song[0] not in self.DownloadList:
                self.DownloadList.append(song[0])

        else:
            song = [i for i in self.yt if str(i['id']) == _id]
            if song[0] not in self.DownloadList:
                self.DownloadList.append(song[0])

                
        if not self.downloading:
            self.downloading = True
            self.downloadSong()

        self.playList.append(song[0])

        if not self.songListShow:
            self.songListShowAni()
        
        self.songList.addList(song[0])
        
    def downloadSong(self):
        if len(self.DownloadList) == 0:
            self.downloading = False
            return
        token = "MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/wapi/clientlog;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/wapi/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/weapi/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/api/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/weapi/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/neapi/clientlog;;__remember_me=true; Max-Age=1296000; Expires=Tue, 21 Jun 2022 03:31:18 GMT; Path=/;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/neapi/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/eapi/feedback;;MUSIC_SNS=; Max-Age=0; Expires=Mon, 06 Jun 2022 03:31:18 GMT; Path=/;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/weapi/feedback;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/api/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/api/feedback;;MUSIC_U=fa99acd715ae82d9462ed3d6edbf280c19b496e0bc1db4694e2065d1d245789ebf35744ebdc80279f852c4a6af253d263f03ae70727669c487c14526381d5553fa25fd6011d05c7586c18b7af633e86b; Max-Age=1296000; Expires=Tue, 21 Jun 2022 03:31:18 GMT; Path=/;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/eapi/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/openapi/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/eapi/clientlog;;__csrf=1d2672d8b607218a27eddcf1a01a0e34; Max-Age=1296010; Expires=Tue, 21 Jun 2022 03:31:28 GMT; Path=/;;NMTID=00OY8_E5LzJC6eY6Ej9hAekFvR6Ay0AAAGBNxEgSg; Max-Age=315360000; Expires=Thu, 03 Jun 2032 03:31:18 GMT; Path=/;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/wapi/clientlog;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/neapi/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/neapi/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/api/clientlog;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/eapi/feedback;;MUSIC_R_T=1486229189929; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/wapi/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/weapi/feedback;;MUSIC_A_T=1486229059031; Max-Age=2147483647; Expires=Sat, 24 Jun 2090 06:45:25 GMT; Path=/openapi/clientlog;"
        
        song = self.DownloadList[0]

        if song["type"] == 0:

            self.getNCMSong.arguments = ["d", "--ncm", f"{token}(<>){song['id']}"]
            self.getNCMSong.start()
        else:

            self.getYTSong.id = song['id']
            self.getYTSong.start()

    def insertSongBtn_Clicked(self, _id, _type):

        if _type == 0:
            song = [i for i in self.ncm if str(i['id']) == _id]
            if song[0] not in self.DownloadList:
                self.DownloadList.append(song[0])

        else:
            song = [i for i in self.yt if str(i['id']) == _id]
            if song[0] not in self.DownloadList:
                self.DownloadList.append(song[0])

                
        if not self.downloading:
            self.downloading = True
            self.downloadSong()

        self.playList.insert(self.np + 1, song[0])

        if not self.songListShow:
            self.songListShowAni()

        self.songList.insertList(song[0], self.np)     

    def addFavoriteBtn_Clicked(self, _id, _type):

        if self.favoriteListShow:
            self.favoriteList.mainListShowAni()
            self.favoriteCloseAni()
        
        song = [i for i in self.ncm if str(i['id']) == _id]

        if len(song) == 0:
            song = [i for i in self.yt if str(i['id']) == _id]
        
        if len(song) == 0:
            song = [i for i in self.playList if str(i['id']) == _id]

        self.addFavoriteList.openAni(song[0])

    def ncmProgress_updated(self, text: str):
        if text.startswith('{'):
            for i in self.playList:
                if i["id"] == self.DownloadList[0]["id"]:
                    i["lrc"] = json.loads(text)["lrc"]
        else:
            self.songList.setProgressBar(self.DownloadList[0]["id"], int(text))

    def ytProgress_updated(self, text: str):
        if text.isdigit():
            self.songList.setProgressBar(self.DownloadList[0]["id"], int(text))

    def ncmDownload_finish(self):
        self.songList.setReady(self.DownloadList[0]["id"])
        self.DownloadList.pop(0)
        self.player_start()
        self.downloadSong()
        print('ncm')

    def ytDownload_finish(self):
        self.songList.setReady(self.DownloadList[0]["id"])
        self.DownloadList.pop(0)
        self.player_start()
        self.downloadSong()
        print('yt')
        

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.searchBar_ani_group.stop()
        self.searchList_ani_group.stop()
        self.favorite_ani_group.stop()
        self.SongList_ani_group.stop()
        self.playerBtn_ani_group.stop()

        self.adj()

    def le_returnPressed(self):
        if self.favoriteListShow:
            self.favoriteList.mainListShowAni()
            self.favoriteCloseAni()

        self.search = 0
        self.yt = []
        self.ncm = []
        self.getYTList.arguments = ["s", "-y", self.le.text()]
        self.getNCMList.arguments = ["s", "--ncm", f"(<>){self.le.text()}"]
        self.getYTList.start()
        self.getNCMList.start()
        if not self.searchBarUP:
            self.searchBarUpAni()
        self.searchListShowAni()
        self.searchList.loadingAniStart()

    def searchYTFinish(self):
        self.search += 1
        self.yt = json.loads(self.getYTList.output)
        if self.search == 2:
            self.searchList.loadingAniFinish(self.yt, self.ncm)

    def searchNCMFinish(self):
        self.search += 1
        self.ncm = json.loads(self.getNCMList.output)
        if self.search == 2:
            self.searchList.loadingAniFinish(self.yt, self.ncm)


    def favoriteBtnClicked(self):
        self.favoriteList.mainListShowAni()
        if not self.searchBarUP:
            self.searchBarUpAni()
            
        if self.favoriteListShow:
            self.favoriteCloseAni()
            if not self.songListShow and not self.searchListShow:
                self.searchBarDownAni()
        else:
            self.favoriteShowAni()

    def songListBtnClicked(self):
        if not self.searchBarUP:
            self.searchBarUpAni()
            
        if self.songListShow:
            self.songListCloseAni()
            if not self.favoriteListShow and not self.searchListShow:
                self.searchBarDownAni()
        else:
            self.songListShowAni()
    
    def settingsBtnClicked(self):
        if self.settingsPageShow:
            self.settingsPageCloseAni()
        else:
            self.settingsPageShowAni()

    def settingsPageShowAni(self):
        self.settingsPage_ani_group.stop()
        self.settingsPageShow = True

        settingsPage_x = self.rim
        settingsPage_y = self.topRim

        self.settingsPage_ani.setEndValue(QPoint(settingsPage_x, settingsPage_y))

        self.settingsPage_Shadow_ani.setEndValue(QPoint(settingsPage_x + self.offset, settingsPage_y + self.offset))

        self.settingsPage_ani_group.start()

    def settingsPageCloseAni(self):
        self.settingsPage_ani_group.stop()
        self.settingsPageShow = False

        settingsPage_x = self.rim
        settingsPage_y = -(self.height() - (self.topRim + self.rim)) - self.offset

        self.settingsPage_ani.setEndValue(QPoint(settingsPage_x, settingsPage_y))

        self.settingsPage_Shadow_ani.setEndValue(QPoint(settingsPage_x + self.offset, settingsPage_y + self.offset))

        self.settingsPage_ani_group.start()

    def playerBtnCloseAni(self):
        self.playerBtn_ani_group.stop()
        self.playerBtnShow = False

        playPauseBtn_x = self.rim
        playPauseBtn_y = self.height()

        skipBtn_x = self.rim + self.margin + self.play_pause_btn.width()
        skipBtn_y = self.height()

        reloadBtn_x = self.rim + self.play_pause_btn.width() + self.skip_btn.width() + self.margin * 2
        reloadBtn_y = self.height()

        self.play_pause_btn_ani.setEndValue(QPoint(playPauseBtn_x, playPauseBtn_y))
        self.play_pause_btn_Shadow_ani.setEndValue(QPoint(playPauseBtn_x + self.offset, playPauseBtn_y + self.offset))

        self.skip_btn_ani.setEndValue(QPoint(skipBtn_x, skipBtn_y))
        self.skip_btn_Shadow_ani.setEndValue(QPoint(skipBtn_x + self.offset, skipBtn_y + self.offset))

        self.reload_btn_ani.setEndValue(QPoint(reloadBtn_x, reloadBtn_y))
        self.reload_btn_Shadow_ani.setEndValue(QPoint(reloadBtn_x + self.offset, reloadBtn_y + self.offset))

        self.playerBtn_ani_group.start()

        if self.searchListShow:
            self.searchListShowAni()

        if self.favoriteListShow:
            self.favoriteShowAni()

    def playerBtnShowAni(self):
        self.playerBtn_ani_group.stop()
        self.playerBtnShow = True
        
        self.play_pause_btn.show()
        self.skip_btn.show()
        self.reload_btn.show()

        searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim + 15 + self.play_pause_btn.width())
        playPauseBtn_x = self.rim
        playPauseBtn_y = self.topRim + self.searchBar_bg.height() + self.margin * 2 + searchList_h

        skipBtn_x = self.rim + self.margin + self.play_pause_btn_Shadow.width()
        skipBtn_y = self.topRim + self.searchBar_bg.height() + self.margin * 2 + searchList_h

        reloadBtn_x = skipBtn_x + self.margin + self.skip_btn_Shadow.width()
        reloadBtn_y = self.topRim + self.searchBar_bg.height() + self.margin * 2 + searchList_h

        self.play_pause_btn_ani.setEndValue(QPoint(playPauseBtn_x, playPauseBtn_y))
        self.play_pause_btn_Shadow_ani.setEndValue(QPoint(playPauseBtn_x + self.offset, playPauseBtn_y + self.offset))

        self.skip_btn_ani.setEndValue(QPoint(skipBtn_x, skipBtn_y))
        self.skip_btn_Shadow_ani.setEndValue(QPoint(skipBtn_x + self.offset, skipBtn_y + self.offset))

        self.reload_btn_ani.setEndValue(QPoint(reloadBtn_x, reloadBtn_y))
        self.reload_btn_Shadow_ani.setEndValue(QPoint(reloadBtn_x + self.offset, reloadBtn_y + self.offset))

        self.playerBtn_ani_group.start()

        if self.searchListShow:
            self.searchListShowAni()

        if self.favoriteListShow:
            self.favoriteShowAni()

    def songListShowAni(self):
        self.SongList_ani_group.stop()
        self.songListShow = True

        self.songList.show()
        self.songListBg.show()
        self.songListBg_Shadow.show()

        songList_x = round(self.width() / 2) + 10
        songList_y = self.topRim + self.searchBar_bg.height() + self.margin

        self.songList_ani.setEndValue(QPoint(songList_x, songList_y))
        self.songListBg_ani.setEndValue(QPoint(songList_x, songList_y))
        self.songListBg_Shadow_ani.setEndValue(QPoint(songList_x + self.offset, songList_y + self.offset))

        self.SongList_ani_group.start()

        if self.searchListShow:
            self.searchListShowAni()
        if not self.searchBarUP:
            self.searchBarUpAni()

    def songListCloseAni(self):
        self.SongList_ani_group.stop()
        self.songListShow = False

        songList_x = self.width()
        songList_y = self.topRim + self.searchBar_bg.height() + self.margin

        self.songList_ani.setEndValue(QPoint(songList_x, songList_y))
        self.songListBg_ani.setEndValue(QPoint(songList_x, songList_y))
        self.songListBg_Shadow_ani.setEndValue(QPoint(songList_x + self.offset, songList_y + self.offset))

        self.SongList_ani_group.start()
        if self.searchListShow:
            self.searchListShowAni()
        if not self.searchListShow and not self.favoriteListShow:
            self.searchBarDownAni()


    def searchListShowAni(self):
        self.searchList_ani_group.stop()
        self.searchListShow = True

        self.searchList.show()
        self.searchListBg.show()
        self.searchListBg_Shadow.show()

        searchList_w = self.width() - self.rim * 2
        searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        searchList_x = self.rim
        searchList_y = self.topRim + self.searchBar_bg.height() + self.margin

        if self.songListShow:
            searchList_w = round(self.width() / 2) - self.rim - 10

        if self.playerBtnShow:
            searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.play_pause_btn.height() + self.margin * 2 + self.rim)

        self.searchList_ani.setEndValue(QRect(searchList_x, searchList_y, searchList_w, searchList_h))

        self.searchListBg_ani.setEndValue(QRect(searchList_x, searchList_y, searchList_w, searchList_h))

        self.searchListBg_Shadow_ani.setEndValue(QRect(searchList_x + self.offset, searchList_y + self.offset, searchList_w, searchList_h))

        self.searchList_ani_group.start()

    def searchListCloseAni(self):
        self.searchList_ani_group.stop()
        self.searchListShow = False

        searchList_x = self.height()
        searchList_y = self.topRim + self.searchBar_bg.height() + self.margin
        searchList_w = self.width() - self.rim * 2
        searchList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)

        self.searchList_ani.setEndValue(QRect(searchList_x, searchList_y, searchList_w, searchList_h))

        self.searchListBg_ani.setEndValue(QRect(searchList_x, searchList_y, searchList_w, searchList_h))

        self.searchListBg_Shadow_ani.setEndValue(QRect(searchList_x + self.offset, searchList_y + self.offset, searchList_w, searchList_h))

        self.searchList_ani_group.start()
    

    def searchBarUpAni(self):
        self.searchBar_ani_group.stop()
        self.searchBarUP = True

        searchBg_w = self.width() - (self.favorite_btn.width() + self.search_btn.width() + self.songList_btn.width() + self.settingsBtn.width() + self.rim * 2 + self.margin * 4)
        searchBg_h = self.searchBar_bg.height()
        searchBg_x = self.rim + self.favorite_btn.width() + self.margin
        searchBg_y = self.topRim

        le_w = self.width() - (self.favorite_btn.width() + self.search_btn.width() + self.songList_btn.width() + self.settingsBtn.width() + self.rim * 2 + self.margin * 4) - 50
        le_h = self.le.height()
        le_x = self.rim + self.favorite_btn.width() + self.margin + 25
        le_y = self.topRim + round((self.searchBar_bg.height() - self.le.height()) / 2)

        self.searchBar_bg_ani.setEndValue(QRect(searchBg_x, searchBg_y, searchBg_w, searchBg_h))
        self.searchBar_bg_Shadow_ani.setEndValue(QRect(searchBg_x + self.offset, searchBg_y + self.offset, searchBg_w, searchBg_h))

        self.le_ani.setEndValue(QRect(le_x, le_y, le_w, le_h))

        self.search_btn_ani.setEndValue(QPoint(self.width() - (self.rim + self.settingsBtn.width() + self.songList_btn.width() + self.search_btn.width() + self.margin * 2), self.topRim))
        self.search_btn_Shadow_ani.setEndValue(QPoint(self.width() - (self.rim + self.settingsBtn.width() + self.songList_btn.width() + self.search_btn.width() + self.margin * 2) + self.offset, self.topRim + self.offset))

        self.searchBar_ani_group.start()

    def searchBarDownAni(self):
        self.searchBar_ani_group.stop()
        self.searchBarUP = False

        searchBg_w = 700
        searchBg_h = 50
        searchBg_x = round((self.width() - searchBg_w) / 2)
        searchBg_y = round((self.height() - searchBg_h) / 2)

        le_w = 650
        le_h = 38
        le_x = round((self.width() - le_w) / 2)
        le_y = round((self.height() - le_h) / 2)

        self.searchBar_bg_ani.setEndValue(QRect(searchBg_x, searchBg_y, searchBg_w, searchBg_h))
        self.searchBar_bg_Shadow_ani.setEndValue(QRect(searchBg_x + self.offset, searchBg_y + self.offset, searchBg_w, searchBg_h))

        self.le_ani.setEndValue(QRect(le_x, le_y, le_w, le_h))

        self.search_btn_ani.setEndValue(QPoint(searchBg_x + searchBg_w + self.margin, searchBg_y))
        self.search_btn_Shadow_ani.setEndValue(QPoint(searchBg_x + searchBg_w + self.margin + self.offset, searchBg_y + self.offset))

        self.searchBar_ani_group.start()
        
    def favoriteShowAni(self):
        self.favorite_ani_group.stop()
        self.favoriteList.show()
        self.favoriteList_Shadow.show()

        favoriteList_w = round(self.width() / 2) - self.rim - 10
        favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        favoriteList_x = self.rim
        favoriteList_y = self.topRim + self.searchBar_bg.height() + self.margin

        if self.playerBtnShow:
            favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.play_pause_btn.height() + self.margin * 2 + self.rim)

        self.favoriteList_ani.setEndValue(QRect(favoriteList_x, favoriteList_y, favoriteList_w, favoriteList_h))
        
        self.favoriteList_Shadow_ani.setEndValue(QRect(favoriteList_x + self.offset, favoriteList_y + self.offset, favoriteList_w, favoriteList_h))

        self.favorite_ani_group.start()

        self.favoriteListShow = True

    def favoriteCloseAni(self):
        self.favorite_ani_group.stop()

        favoriteList_w = round(self.width() / 2) - self.rim - 10
        favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.margin + self.rim)
        favoriteList_x = -self.favoriteList.width() - self.offset
        favoriteList_y = self.topRim + self.searchBar_bg.height() + self.margin

        if self.playerBtnShow:
            favoriteList_h = self.height() - (self.topRim + self.searchBar_bg.height() + self.play_pause_btn.height() + self.margin * 2 + self.rim)

        self.favoriteList_ani.setEndValue(QRect(favoriteList_x, favoriteList_y, favoriteList_w, favoriteList_h))
        
        self.favoriteList_Shadow_ani.setEndValue(QRect(-self.favoriteList.width(), favoriteList_y + self.offset, favoriteList_w, favoriteList_h))

        self.favorite_ani_group.start()

        self.favoriteListShow = False

    def closeEvent(self, event):
        if self.player_status != "close":
            return
            event.ignore()
            self.sendClose.start()

            s = QTimer(self)
            s.timeout.connect(lambda: __close(self, s))
            s.start(10)
            def __close(self, s):
                print(1010)
                if self.player_status == "close":
                    s.stop()
                    self.close()






        

