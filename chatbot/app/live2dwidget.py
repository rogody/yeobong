import os
import sys
from PIL import Image
import numpy as np
from PySide6.QtCore import QTimerEvent, Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import OpenGL.GL as gl
from PySide6.QtWidgets import (QApplication, 
                               QWidget, QMainWindow, 
                               QPushButton, QTextEdit, QLineEdit,
                               QVBoxLayout, QHBoxLayout
                               )
from PySide6.QtGui import QGuiApplication ,QMouseEvent, QCursor

import live2d.v3 as live2d


CURRENT_DIRECTORY = os.path.split(__file__)[0]
PARENT_DIRECTORY = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
MAO_MODEL_DIRECTORY = os.path.join(PARENT_DIRECTORY,  "Resources/mao_pro_en/runtime/mao_pro.model3.json")
EPSILON_MODEL_DIRECTORY = os.path.join(PARENT_DIRECTORY, "Resources/Epsilon/runtime/Epsilon.model3.json")


# --- 1. 감정 → expression ID 매핑 ---

# 실제 어떤 exp가 어떤 표정인지 몰라도 일단 이렇게 넣고
# 버튼 눌러보면서 "아 이게 happy네" 식으로 조정하면 됨.
EMOTION_EXPRESSION_ID = {
    "neutral": "exp_01",
    "happy": "exp_02",
    "sad": "exp_05",
}


def callback():
    print("motion end")


class Live2DWidget(QOpenGLWidget):

    def __init__(self) -> None:
        live2d.init()
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
            self.model_path = EPSILON_MODEL_DIRECTORY
        #elif(name == "huohuo"):
            #self.model_path = HUOHUO_MODEL_DIRECTORY
        #elif(name=="frieren"):
            #self.model_path = FRIEREN_MODEL_DIRECTORY

    def initializeGL(self) -> None:
        live2d.glewInit()

        self.model = live2d.LAppModel()

        self.model.LoadModelJson(self.model_path)
        
        #fps 120
        self.startTimer(int(1000 / 120))

    def resizeGL(self, w: int, h: int) -> None:

        if self.model:
            self.model.Resize(w, h)

    def paintGL(self) -> None:
        live2d.clearBuffer()

        self.model.Update()

        self.model.Draw()
        '''
        if not self.read:
            self.savePng('screenshot.png')

            self.read = True
            '''
    '''
    def savePng(self, fName):
        data = gl.glReadPixels(0, 0, self.width(), self.height(), gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        data = np.frombuffer(data, dtype=np.uint8).reshape(self.height(), self.width(), 4)
        data = np.flipud(data)
        new_data = np.zeros_like(data)
        for rid, row in enumerate(data):
            for cid, col in enumerate(row):
                color = None
                new_data[rid][cid] = col
                if cid > 0 and data[rid][cid - 1][3] == 0 and col[3] != 0:
                    color = new_data[rid][cid - 1]
                elif cid > 0 and data[rid][cid - 1][3] != 0 and col[3] == 0:
                    color = new_data[rid][cid]
                if color is not None:
                    color[0] = 255
                    color[1] = 0
                    color[2] = 0
                    color[3] = 255
                color = None
                if rid > 0:
                    if data[rid - 1][cid][3] == 0 and col[3] != 0:
                        color = new_data[rid - 1][cid]
                    elif data[rid - 1][cid][3] != 0 and col[3] == 0:
                        color = new_data[rid][cid]
                elif col[3] != 0:
                    color = new_data[rid][cid]
                if color is not None:
                    color[0] = 255
                    color[1] = 0
                    color[2] = 0
                    color[3] = 255
        img = Image.fromarray(new_data, 'RGBA')
        img.save(fName)'''
            
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
            print("pressed")
            #self.rotate = self.rotate+90
            #self.model.Rotate(self.rotate)
            #if(self.model.IsMotionFinished() == True):
                #self.model.StartRandomMotion()
                #self.model.SetRandomExpression()

    def mouseReleaseEvent(self, event):
        x, y = event.scenePosition().x(), event.scenePosition().y()
        # if self.isInL2DArea(x, y):
        if self.isInLA:
            # self.model.Touch(x, y)
            pass
            self.clickInLA = False
            print("released")

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