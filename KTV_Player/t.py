import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class Video(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 720)
        self.videoPlayer = QMediaPlayer(self)
        self.musicPlayer = QMediaPlayer(self)
        self.audioOutput = QAudioOutput(self)

        self.musicPlayer.setAudioOutput(self.audioOutput)

        self.videoWidget = QVideoWidget(self)

        self.videoPlayer.setVideoOutput(self.videoWidget)

        self.musicPlayer.mediaStatusChanged.connect(lambda state: self.stateChange(state))

        self.musicPlayer.errorOccurred.connect(lambda error, errorString: self.playerError(error, errorString))

        self.adj()

    def playerError(self, error, errorString):
        print(error)
        print(errorString)

    def adj(self):
        self.videoWidget.resize(self.width(), self.height())
        self.videoWidget.move(0, 0)

    def play_(self):
        self.musicPlayer.setSource(QUrl.fromLocalFile(f"./cache/yt/GhkOc-B6W8c.mp3"))
        self.videoPlayer.setSource(QUrl.fromLocalFile(f"./cache/yt/GhkOc-B6W8c.webm"))
        self.musicPlayer.play()
        self.videoPlayer.play()

    def stateChange(self, state: QMediaPlayer):
        print(state)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Video()
    main_window.show()
    main_window.play_()
    sys.exit(app.exec())
