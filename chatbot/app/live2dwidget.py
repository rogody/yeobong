
from PySide6.QtCore import QTimerEvent, Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import OpenGL.GL as gl
from PySide6.QtGui import QGuiApplication ,QMouseEvent, QCursor

import live2d.v3 as live2d
from chatbot.app import paths
from pathlib import Path

EPSILON_MODEL_DIRECTORY = paths.RESOURCES_DIR / "Epsilon" / "runtime" / "Epsilon.model3.json"

def callback():
    print("motion end")


class Live2DWidget(QOpenGLWidget):

    def __init__(self) -> None:
        super().__init__()
        self.isInLA = False
        self.clickInLA = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.a = 0
        self.resize(400, 500)
        self.read = False
        self.clickX = -1
        self.clickY = -1
        self.model: live2d.LAppModel | None = None
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()
    
    def set_model(self, name:str):
        if(name == "epsilon"):
            print("Set Epsilon Model")
            self.model_path = EPSILON_MODEL_DIRECTORY

    def initializeGL(self) -> None:
        print("Live2D initializeGL")
        live2d.glInit()
    
        # 경로 검증
        if not hasattr(self, "model_path") or self.model_path is None:
            print("Live2D model_path 가 설정되지 않았습니다.")
            return
    
        if not Path(self.model_path).exists():
            print("Live2D 모델 파일을 찾을 수 없습니다:", self.model_path)
            return
    
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(str(self.model_path))
    
        # fps 120
        self.startTimer(int(1000 / 120))

    def resizeGL(self, w: int, h: int) -> None:

        if self.model:
            self.model.Resize(w, h)

    def paintGL(self) -> None:
        live2d.clearBuffer()
        if self.model is None:
            print("Live2D paintGL called but model is None")
            return

        self.model.Update()

        self.model.Draw()
            
    def timerEvent(self, a0: QTimerEvent | None) -> None:
        if not self.isVisible():
            return

        if self.a == 0:  
            self.model.StartMotion("TapBody", 0, live2d.MotionPriority.FORCE, onFinishMotionHandler=callback)
            self.a += 1

        local_x, local_y = QCursor.pos().x() - self.x(), QCursor.pos().y() - self.y()
        if self.isInL2DArea(local_x, local_y):
            self.isInLA = True
            # print("in l2d area")
        else:
            self.isInLA = False
            # print("out of l2d area")

        self.update()

    def isInL2DArea(self, click_x, click_y):
        h = self.height()
        alpha = gl.glReadPixels(click_x * self.systemScale, (h - click_y) * self.systemScale, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)[3]
        return alpha > 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x, y = event.scenePosition().x(), event.scenePosition().y()
        # MOUSE POSITION
        if self.isInL2DArea(x, y):
            self.clickInLA = True
            self.clickX, self.clickY = x, y


    def mouseReleaseEvent(self, event):
        x, y = event.scenePosition().x(), event.scenePosition().y()
        if self.isInLA:
            pass
            self.clickInLA = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x, y = event.scenePosition().x(), event.scenePosition().y()
        if self.clickInLA:
            self.move(int(self.x() + x - self.clickX), int(self.y() + y - self.clickY))
        xp, yp = event.globalPosition().x() - self.x(), event.globalPosition().y() - self.y()
        self.model.Drag(xp, yp)   
        
    def set_motion(self, emotion):
        if not self.model:
            return
        
        if emotion == "anger":
            self.model.StartMotion("special", 3, 1)
        elif emotion == "disgust":
            self.model.StartMotion("special", 4, 1)
            self.model.SetExpression("f02")
        elif emotion == "fear":
            self.model.StartMotion("special", 1, 1)
            self.model.SetExpression("Sad")
        elif emotion == "joy":
            self.model.StartMotion("normal", 3, 1)
        elif emotion == "neutral":
            self.model.StartMotion("Idle", 0, 2)
        elif emotion == "sadness":
            self.model.StartMotion("special", 2, 1)
        elif emotion == "surprise":
            self.model.StartMotion("normal", 6, 2)
            self.model.SetExpression("Surprised")