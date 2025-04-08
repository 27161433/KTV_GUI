# coding:utf-8
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import cv2
from re import match
from time import time
import numpy as np
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase, QResizeEvent, QKeyEvent, QCloseEvent, QMouseEvent, QCursor, QEnterEvent, QWheelEvent
from PySide6.QtCore import Qt, QUrl, QEasingCurve, QThread, Signal, QTimer, QPropertyAnimation, QPoint, Property, QPointF, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import json
os.environ['QT_MEDIA_BACKEND'] = 'windows'

class LrcTimer(QTimer):
    timeout = Signal()
    updateLrcEvent = Signal()

    def __init__(self):
        super().__init__()
        self.init()
        self.setInterval(1)
        self.timeout.connect(self.updateLrc)

    def init(self):
        self.lrc = [
            '',
            '',
            '',
            '',
            '',
            ''
        ]
        self.lrcIn = []
        self.startTime = 0
        self.nowTime = 0
        self.first = True
        self.aniTime = 1
        self.pausetime = 0

    def setLrc(self, lrc):
        self.lrcIn = lrc
        if len(self.lrcIn) > 0:
            self.lrc[3] = self.lrcIn[0][1]
        if len(self.lrcIn) > 1:
            self.lrc[4] = self.lrcIn[1][1]
        if len(self.lrcIn) > 2:
            self.lrc[5] = self.lrcIn[2][1]

    def pause(self):
        self.pausetime = int(time() * 100)
        self.stop()

    def play(self):
        self.startTime += int(time() * 100) - self.pausetime
        self.start()

    def updateLrc(self):

        t = int(time() * 100)
        if self.nowTime == t // 10:
            return
        if self.first:
            self.startTime = t
            self.first = False

        for i in range(len(self.lrcIn)):
            if t == self.startTime + self.lrcIn[i][0]:
                self.nowTime = t // 10
                if not (i + 1 >= len(self.lrcIn)):
                    tr = (self.lrcIn[i + 1][0] - self.lrcIn[i][0])
                    self.aniTime = tr if tr < 1000 else 1000
                else:
                    self.aniTime = 1000

                self.lrc[0] = '' if i - 2 < 0 else self.lrcIn[i - 2][1]
                self.lrc[1] = '' if i - 1 < 0 else self.lrcIn[i - 1][1]
                self.lrc[2] = self.lrcIn[i][1]
                self.lrc[3] = '' if i + 1 >= len(self.lrcIn) else self.lrcIn[i + 1][1]
                self.lrc[4] = '' if i + 2 >= len(self.lrcIn) else self.lrcIn[i + 2][1]
                self.lrc[5] = '' if i + 3 >= len(self.lrcIn) else self.lrcIn[i + 3][1]

                self.updateLrcEvent.emit()

                if "纯音乐，请欣赏" in self.lrcIn[i][1]:
                    return self.stop()


class AniLrc(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet('font-weight: bold; color: white; background: transparent;')

    def setFontSize(self, size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    def getFontSize(self):
        pass

    fontSize = Property(int, getFontSize, setFontSize)


class NcmWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        self.fontName = fontDb.applicationFontFamilies(fontId)[0]
        self.mainFont = QFont(self.fontName, 50)
        self.textFont = QFont(self.fontName, 30)

        self.bgLabel = QLabel(self)
        self.bgLabel.setScaledContents(True)
        self.adjustBg()

        self.lrcTimer = LrcTimer()
        self.lrcTimer.updateLrcEvent.connect(self.updateLrc)

        self.lrc0 = AniLrc(self)
        self.lrc1 = AniLrc(self)
        self.lrc2 = AniLrc(self)
        self.lrc3 = AniLrc(self)
        self.lrc4 = AniLrc(self)
        self.lrc5 = AniLrc(self)

        self.lrc0.setFont(self.textFont)
        self.lrc1.setFont(self.textFont)
        self.lrc2.setFont(self.mainFont)
        self.lrc3.setFont(self.textFont)
        self.lrc4.setFont(self.textFont)
        self.lrc5.setFont(self.textFont)

        self.adjustLrc()

    def timerState(self):
        return self.lrcTimer.isActive()

    def stop(self):
        self.lrcTimer.stop()

    def pause(self):
        self.lrcTimer.pause()

    def play(self):
        self.lrcTimer.play()

    def setLrc(self):
        self.lrcTimer.init()

        lrc = data['lrc'].split("\n")

        def n(i):
            pattern = r'\d{2}:\d{2}:\d{2}'
            text = i.split("[")[1].split("]")[0].replace(".", ":")

            if match(pattern, text):
                t = text.split(":")
                if len(t[2]) > 2:
                    t[2] = t[2][:-1]
                if "-" in t[2]:
                    t[2] = "00"
                return ((int(t[0]) * 60 + int(t[1])) * 100 + int(t[2]))
            else:
                return 0

        result = [[n(i), i.split("]")[1]] for i in lrc if i and i.split("]")[1]]

        self.lrcTimer.setLrc(result)

        self.lrc0.setText(self.lrcTimer.lrc[0])
        self.lrc1.setText(self.lrcTimer.lrc[1])
        self.lrc2.setText(self.lrcTimer.lrc[2])
        self.lrc3.setText(self.lrcTimer.lrc[3])
        self.lrc4.setText(self.lrcTimer.lrc[4])
        self.lrc5.setText(self.lrcTimer.lrc[5])
        self.adjustLrc()

    def lrcStart(self):
        self.lrcTimer.start()

    def setBg(self, bg):
        self.bgLabel.setPixmap(QPixmap.fromImage(bg))
        self.adjustBg()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustBg()
        self.adjustLrc()

    def adjustBg(self):
        pixmap = self.bgLabel.pixmap()
        if pixmap.isNull():
            return

        w = self.width()
        h = self.height()
        o = w
        if w < h:
            o = h

        ncmbg.scaled(o, o, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.bgLabel.setPixmap(pixmap)

        self.bgLabel.resize(o, o)
        if w > h:
            self.bgLabel.move(0, -(o - h) // 2)
        else:
            self.bgLabel.move(-(o - w) // 2, 0)

    def adjustLrc(self):

        self.lrc0.resize(self.width(), self.height())
        self.lrc1.resize(self.width(), self.height())
        self.lrc2.resize(self.width(), self.height())
        self.lrc3.resize(self.width(), self.height())
        self.lrc4.resize(self.width(), self.height())
        self.lrc5.resize(self.width(), self.height())

        self.lrc0.move(self.width() // 2 - self.lrc0.width() // 2, self.height() // 2 - self.lrc0.height() // 2 - self.height() // 10 * 4)
        self.lrc1.move(self.width() // 2 - self.lrc1.width() // 2, self.height() // 2 - self.lrc1.height() // 2 - self.height() // 10 * 2)
        self.lrc2.move(self.width() // 2 - self.lrc2.width() // 2, self.height() // 2 - self.lrc2.height() // 2)
        self.lrc3.move(self.width() // 2 - self.lrc3.width() // 2, self.height() // 2 - self.lrc3.height() // 2 + self.height() // 10 * 2)
        self.lrc4.move(self.width() // 2 - self.lrc4.width() // 2, self.height() // 2 - self.lrc4.height() // 2 + self.height() // 10 * 4)
        self.lrc5.move(self.width() // 2 - self.lrc4.width() // 2, self.height() // 2 - self.lrc4.height() // 2 + self.height() // 10 * 6)

    def updateLrc(self):
        w = self.width() // 2 - self.lrc0.width() // 2
        h = self.height() // 2 - self.lrc0.height() // 2
        self.startAnimation(self.lrc0, w, h - self.height() // 10 * 6, self.lrcTimer.lrc[0])
        self.startAnimation(self.lrc1, w, h - self.height() // 10 * 4, self.lrcTimer.lrc[1])
        self.startAnimation(self.lrc2, w, h - self.height() // 10 * 2, self.lrcTimer.lrc[2], 50, 30)
        self.startAnimation(self.lrc3, w, h, self.lrcTimer.lrc[3], 30, 51)
        self.startAnimation(self.lrc4, w, h + self.height() // 10 * 2, self.lrcTimer.lrc[4])
        self.startAnimation(self.lrc5, w, h + self.height() // 10 * 4, self.lrcTimer.lrc[5])

    def startAnimation(self, label, x, y, text, st=0, ed=0):
        ani = QPropertyAnimation(label, b"pos", self)
        ani.setDuration(round(self.lrcTimer.aniTime * 1.5))
        ani.setStartValue(QPoint(label.x(), label.y()))
        ani.setEndValue(QPoint(x, y))
        ani.setEasingCurve(QEasingCurve.Type.OutQuart)
        ani.start()
        ani.finished.connect(lambda: self.aniF(text, label, ani))

        if st:
            fontAni = QPropertyAnimation(label, b"fontSize", self)
            fontAni.setDuration(round(self.lrcTimer.aniTime * 1.5))
            fontAni.setStartValue(st)
            fontAni.setEndValue(ed)
            fontAni.setEasingCurve(QEasingCurve.Type.OutQuart)
            fontAni.start()
            fontAni.finished.connect(lambda: self.fontAniF(label, st, fontAni))

    def fontAniF(self, label: QLabel, st: int, ani: QPropertyAnimation):
        font = label.font()
        font.setPointSize(st)
        label.setFont(font)
        ani.deleteLater()

    def aniF(self, text, label: QLabel, ani: QPropertyAnimation):
        label.setText(text)
        ani.deleteLater()
        self.adjustLrc()

    def aniFontUpdate(self, label):
        label.setFont(QFont(self.fontName, 20))


class IconLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._type = ""
        self.setStyleSheet('background: transparent;')

    def setIcon(self, Icon, enterIcon, pressIcon):
        self.Icon = Icon
        self.enterIcon = enterIcon
        self.pressIcon = pressIcon
        self.setPixmap(QPixmap.fromImage(Icon))
        self.adjustSize()

    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)
        self.setPixmap(QPixmap.fromImage(self.enterIcon))

    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)
        self.setPixmap(QPixmap.fromImage(self.Icon))

    def setType(self, _type):
        self._type = _type

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        super().mousePressEvent(ev)
        if ev.button() == Qt.MouseButton.LeftButton:
            self.setPixmap(QPixmap.fromImage(self.pressIcon))
            


    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        if ev.button() == Qt.MouseButton.LeftButton:
            pos = self.mapFromGlobal(self.cursor().pos())
            if pos.x() < 0 or pos.x() > self.width() or pos.y() < 0 or pos.y() > self.height():
                return
            
            match self._type:
                case "minimize":
                    player.showMinimized()
                case "maximize":
                    if player.isFullScreen():
                        player.showNormal()
                        player.show()
                    else:
                        player.showFullScreen()
                case "close":
                    player.close()    

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pass



class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        iconSize = 20

        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]
        self.titleBarFont = QFont(fontName, 15)

        self.titleBarBG = QLabel(self)
        self.titleBarBG.setStyleSheet('background-color: rgb(87, 174, 255);')

        self.titleBarTitle = QLabel(self)
        self.titleBarTitle.setFont(self.titleBarFont)
        self.titleBarTitle.setText(f"F11: 全螢幕模式  F8: 切歌  SPACE/F7: 暫停  正在播放: ")
        self.titleBarTitle.setStyleSheet('background: transparent; font-weight: bold; color: white;')
        self.titleBarTitle.move(10, 0)
        self.titleBarTitle.adjustSize()

        self.title = QLabel(self)
        self.title.setFont(self.titleBarFont)
        self.title.setText(data['title'])
        self.title.setStyleSheet('background: transparent; font-weight: bold; color: white;')


        def icon(path): return QImage(path).scaled(iconSize, iconSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.iconBg = QLabel(self)
        self.iconBg.resize(iconSize * 3 + 10 + 15 * 2 + 10, self.height())
        self.iconBg.setStyleSheet('background-color: rgb(87, 174, 255);')

        self.MinimizeIcon = IconLabel(self)
        self.MinimizeIcon.setIcon(icon("./img/light_minimize.png"), icon("./img/minimize.png"), icon("./img/press_minimize.png"))
        self.MinimizeIcon.setType("minimize")

        self.MaximizeIcon = IconLabel(self)
        self.MaximizeIcon.setIcon(icon("./img/light_maximize.png"), icon("./img/maximize.png"), icon("./img/press_maximize.png"))
        self.MaximizeIcon.setType("maximize")

        self.CloseIcon = IconLabel(self)
        self.CloseIcon.setIcon(icon("./img/light_close.png"), icon("./img/close.png"), icon("./img/press_close.png"))
        self.CloseIcon.setType("close")

        self.adj()

    def setText(self, text):
        self.titleBarTitle.setText(text)
        self.titleBarTitle.adjustSize()

    def setTitle(self, title):
        self.title.setText(title)
        self.title.adjustSize()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.adj()
        return super().resizeEvent(event)
    
    def adj(self):
        self.titleBarTitle.adjustSize()
        self.titleBarBG.resize(self.width(), self.height())
        self.title.move(10 + self.titleBarTitle.width(), 0)

        self.iconBg.move(self.width() - self.iconBg.width(), 0)

        self.CloseIcon.move(self.width() - self.CloseIcon.width() - 10, round((self.height() - self.CloseIcon.height()) / 2))
        self.MaximizeIcon.move(self.width() - self.MaximizeIcon.width() * 2 - 10 - 15, round((30 - self.MaximizeIcon.height()) / 2))
        self.MinimizeIcon.move(self.width() - self.MinimizeIcon.width() * 3 - 10 - 15 * 2, round((30 - self.MinimizeIcon.height()) / 2))


class Log(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        fontDb = QFontDatabase
        fontId = fontDb.addApplicationFont("Roboto-Regular.ttf")
        fontName = fontDb.applicationFontFamilies(fontId)[0]
        custom_font = QFont(fontName, 12)

        self.setFixedSize(300, 150)
        self.setStyleSheet("background: white")

        self.bg = QLabel(self)
        self.bg.resize(self.width(), self.height())

        self.log = QLabel("該歌曲無法播放\n點擊確認播放下一首", self)
        self.log.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log.setFont(custom_font)
        self.log.adjustSize()
        self.log.move((self.width() - self.log.width()) // 2, (self.height() - self.log.height()) // 4)

        self.ok_btn = QPushButton(self)
        self.ok_btn.setText("確認")
        self.ok_btn.setFont(custom_font)
        self.ok_btn.setStyleSheet('background-color: rgb(87, 174, 255);')
        self.ok_btn.adjustSize()
        self.ok_btn.move((self.width() - self.ok_btn.width()) // 2, (self.height() - self.ok_btn.height()) // 4 * 3)

        self.ok_btn.clicked.connect(self.btn_clicked)

    def btn_clicked(self):
        self.hide()
        player.mainWidget.show()
        write("next_song")



class Video(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.puase = 0
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background: black")

        self.volume = 1
        self.server = CreatServer()
        self.server.play_yt.connect(self.checkType)
        self.server.pause.connect(self.pause)
        #self.server.stop.connect(self.stop)
        self.server._reload.connect(self.reLoad)
        self.server._close.connect(self._close)

        self.server.start()

        self.videoPlayer = QMediaPlayer(self)
        self.musicPlayer = QMediaPlayer(self)
        self.audioOutput = QAudioOutput(self)
        self.mainWidget = QWidget(self)
        #self.mainWidget.setStyleSheet("background: black")


        self.musicPlayer.setAudioOutput(self.audioOutput)

        self.ncmWidget = NcmWidget(self.mainWidget)

        self.videoWidget = QVideoWidget(self.mainWidget)

        self.videoPlayer.setVideoOutput(self.videoWidget)

        self.musicPlayer.mediaStatusChanged.connect(lambda state: self.stateChange(state))

        self.musicPlayer.errorOccurred.connect(lambda error, errorString: self.playerError(error, errorString))

        self.titleBar = TitleBar(self)

        self.log = Log(self)
        self.log.hide()

        self.adj()

        self.timer = QTimer()
        self.timer.timeout.connect(self.checkMousePosition)
        self.timer.start(100)

    def wheelEvent(self, event: QWheelEvent) -> None:
            # super().wheelEvent(event)
        angle_y = event.angleDelta().y()

        if angle_y > 0:
            if self.volume + 0.05 > 1:
                self.volume = 1
            self.volume += 0.05
            self.audioOutput.setVolume(self.volume)
        elif angle_y < 0:
            if self.volume - 0.05 < 0:
                self.volume = 0
            self.volume -= 0.05
            self.audioOutput.setVolume(self.volume)



    def checkMousePosition(self):
        if not self.isFullScreen():
            return
        
        self.timer.stop()

        position = QCursor.pos()
        x = position.x()
        y = position.y()

        if y <= 30 and x >= 0 and x <= self.width():
            self.titleBarShowAnimation(self.titleBar, 0)
            self.titleBarShowAnimation(self.mainWidget, 30, True)
        else:
            self.titleBarShowAnimation(self.titleBar, -30)
            self.titleBarShowAnimation(self.mainWidget, 0, True)

    def playerError(self, error, errorString):
        #print(error)
        #print(errorString)
        pass

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adj()


    def adj(self):

        h = 0

        if not self.isFullScreen():
            h = 30
            self.resize(1280, 720 + h)
            self.titleBar.move(0, 0)
        else:
            self.titleBar.move(0, -30)

        self.mainWidget.resize(self.width() * 2, self.height())
        self.mainWidget.move(self.width() * - data['type'], h)

        self.ncmWidget.resize(self.width(), self.height() - h)
        self.ncmWidget.move(0, 0)

        self.videoWidget.resize(self.width(), self.height() - h)
        self.videoWidget.move(self.width(), 0)
        
        self.titleBar.resize(self.width(), 30)

        self.log.move((self.width() - self.log.width()) // 2, (self.height() - self.log.height()) // 2)

    def titleBarShowAnimation(self, label, y, fin=False):
        stv = QPoint(label.x(), label.y())
        edv = QPoint(label.x(), y)
        if stv == edv:
            self.timer.start()
            return
        ani = QPropertyAnimation(label, b"pos", self)
        ani.setDuration(500)
        ani.setStartValue(stv)
        ani.setEndValue(edv)
        ani.setEasingCurve(QEasingCurve.Type.OutQuart)
        ani.start()
        if fin:
            ani.finished.connect(self.titleBarAniF)

    def titleBarAniF(self):
        self.timer.start()

    def checkType(self):

        self.ncmWidget.stop()
        self.videoPlayer.stop()
        self.musicPlayer.stop()

        self.timer_ = QTimer()
        self.timer_.timeout.connect(self.checkType_)
        self.timer_.start(500)

    def checkType_(self):
        self.timer_.stop()
        if  data["status"] == "err":
            self.mainWidget.hide()
            self.log.show()
            return
        if self.isFullScreen():
            self.titleBar.setTitle(data["title"])
        else:
            self.titleBar.setTitle(data["title"])

        if data['type']:
            self.ytMode()
        else:
            self.ncmMode()

    def ncmMode(self):
        global ncmbg

        filePath = f"./cache/ncm/re{data['id']}.jpg"
        if not os.path.isfile(filePath):
            img = cv2.imread(f"./cache/ncm/{data['id']}.jpg")

            blurImg = cv2.GaussianBlur(img, (51, 51), 0)

            height, width, channels = img.shape
            grayMask = np.zeros((height, width, channels), dtype=np.uint8)
            grayMask.fill(100)

            output = cv2.addWeighted(blurImg, 0.7, grayMask, 0, 0)

            cv2.imwrite(filePath, output)

        ncmbg = QImage(filePath)

        self.ncmWidget.setBg(ncmbg)
        self.ncmWidget.setLrc()
        self.musicPlayer.setSource(QUrl.fromLocalFile(f"./cache/ncm/{data['id']}.mp3"))
        self.startAni()

    def startAni(self):
        h = 0
        if not self.isFullScreen():
            h = 30

        stv = QPoint(self.mainWidget.x(), self.mainWidget.y())
        edv = QPoint(self.width() * - data['type'], h)

        if stv == edv:
            self.musicPlayer.play()
            if data['type']:
                self.videoPlayer.play()
            self.adj()
            return

        ani = QPropertyAnimation(self.mainWidget, b"pos", self)
        ani.setDuration(1000)
        ani.setStartValue(stv)
        ani.setEndValue(edv)
        ani.setEasingCurve(QEasingCurve.Type.OutQuart)
        ani.start()
        ani.finished.connect(lambda: self.aniF(ani))

    def aniF(self, ani):
        ani.deleteLater()

        self.musicPlayer.play()
        if data['type']:
            self.videoPlayer.play()

        self.adj()

    def ytMode(self):
        self.musicPlayer.setSource(QUrl.fromLocalFile(f"./cache/yt/{data['id']}.mp3"))
        self.videoPlayer.setSource(QUrl.fromLocalFile(f"./cache/yt/{data['id']}.webm"))
        self.startAni()


    def stateChange(self, state: QMediaPlayer):
        global songCount
        #print(state)
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            write("next_song")

            if self.ncmWidget.timerState:
                self.ncmWidget.stop()
                #print('stop')
        elif state == QMediaPlayer.MediaStatus.BufferedMedia and not data['type']:
            self.ncmWidget.lrcStart()

    def pause(self):
        if not self.puase:
            self.videoPlayer.pause()
            self.musicPlayer.pause()
            self.ncmWidget.pause()
            self.puase = 1
        else:
            self.videoPlayer.play()
            self.musicPlayer.play()
            self.ncmWidget.play()
            self.puase = 0

    def keyPressEvent(self, event: QKeyEvent) -> None:
        global songCount
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Enter:
            self.reLoad()
        if event.key() == Qt.Key.Key_Space:
            self.pause()
        if event.key() == Qt.Key.Key_Plus:
            self.ncmWidget.stop()
            self.videoPlayer.stop()
            self.musicPlayer.stop()
            write("next_song")


        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self.titleBar.setText(f"F11: 全螢幕模式  F8: 切歌  SPACE/F7: 暫停  正在播放: ")
            else:
                self.showFullScreen()
                self.titleBar.setText(f"F11/ESC: 離開全螢幕模式  F8: 切歌  SPACE/F7: 暫停  正在播放: ")

        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.titleBar.setText(f"F11: 全螢幕模式  F8: 切歌  SPACE/F7: 暫停  正在播放: ")

    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.last_mouse_position = event.globalPosition()
        
        elif event.buttons() == Qt.MouseButton.MiddleButton:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.last_mouse_position and not self.isFullScreen():
                delta = event.globalPosition() - self.last_mouse_position
                new_position = QPointF(self.pos()) + delta
                self.move(new_position.toPoint())
                self.last_mouse_position = event.globalPosition()

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
        self.videoPlayer.stop()
        self.musicPlayer.stop()
        self.server.terminate()

    def reLoad(self):
        self.ncmWidget.stop()
        self.videoPlayer.stop()
        self.musicPlayer.stop()
        self.checkType()

    def _close(self):
        player.close()


class CreatServer(QThread):
    play_yt = Signal()
    pause = Signal()
    stop = Signal()
    _reload = Signal()
    _close = Signal()
    def __init__(self):
        super().__init__()

    def run(self):
        global data
        write("finish")
        while True:
            d = sys.stdin.readline().strip()
            
            if d.startswith('{'):
                data = json.loads(d)
                self.play_yt.emit()
            elif d == "pause":
                self.pause.emit()
            elif d == "stop":
                self.stop.emit()
            elif d == "reload":
                self._reload.emit()
            elif d == "close":
                self._close.emit()


def write(text):
    print(text)
    out.flush()

data = {
    "id": "null",
    "img": "null",
    "title": "null",
    "artis": "null",
    "lrc": {},
    "dt": 0,
    "type": 0,
    "status": "null"
}
out = sys.stdout
app = QApplication(sys.argv)
player = Video()
player.resize(1280, 720)
player.show()

sys.exit(app.exec())
