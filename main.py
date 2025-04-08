import sys
import math
import threading
import os
#import cv2
from re import match
from time import time
#import yt_dlp as ytdl
#import numpy as np
#from requests import get
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QMainWindow, QVBoxLayout, QHBoxLayout, QScrollArea, QLineEdit, QMenu
from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase, QMovie, QResizeEvent, QMouseEvent, QKeyEvent, QAction, QCursor
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudio, QMediaFormat
from PySide6.QtMultimediaWidgets import QVideoWidget

from tools import Window

QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
app = QApplication(sys.argv)
window = Window()
window.resize(1280, 720)
window.show()

sys.exit(app.exec())
