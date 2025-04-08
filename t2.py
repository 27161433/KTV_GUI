from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QImage
from PySide6.QtCore import QTimer, Qt
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

class GLWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(6)  # 60 frames per second

    def update_animation(self):
        self.time += 0.01 / 2
        if self.time > 1:
            self.time = 0
        self.update()  # this will trigger paintGL

    def initializeGL(self):
        glClearColor(0, 0, 0, 1)
        self.init_texture()

    def init_texture(self):
        image = QImage('./img/t.jpg')
        image = image.mirrored(False, True)  # Flip the image vertically
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width(), image.height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, image.bits())
        glGenerateMipmap(GL_TEXTURE_2D)  # Generate mipmaps
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        self.aspect_ratio = image.width() / image.height()

    def paintGL(self):
        x_pos = self.easing_function(self.time) - 0.5
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-0.5 * self.aspect_ratio + x_pos, -0.5, 0)
        glTexCoord2f(1, 0); glVertex3f(0.5 * self.aspect_ratio + x_pos, -0.5, 0)
        glTexCoord2f(1, 1); glVertex3f(0.5 * self.aspect_ratio + x_pos, 0.5, 0)
        glTexCoord2f(0, 1); glVertex3f(-0.5 * self.aspect_ratio + x_pos, 0.5, 0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def easing_function(self, t):
        # This is a simple easing function that creates a slow-out effect
        return 1 - (1 - t) * (1 - t) * (1 - t)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

class MainWindow(QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setCentralWidget(widget)

if __name__ == '__main__':
    app = QApplication([])
    widget = GLWidget()
    window = MainWindow(widget)
    window.show()
    app.exec()
