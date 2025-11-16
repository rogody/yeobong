from pathlib import Path
import math
import time
import os
import sys

from chatbot.modules.llm_model import LLModel
from .controller import ChatController

from OpenGL.GL import (
    glClearColor,
    glClear,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
)

import live2d.v3 as live2d
from live2d.v3 import StandardParams

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLineEdit,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

CURRENT_DIRECTORY = os.path.split(__file__)[0]
PARENT_DIRECTORY = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))
MODEL_DIRECTORY = os.path.join(PARENT_DIRECTORY,  "Resources\mao_pro_en\\runtime\\mao_pro.model3.json")


# --- 1. 감정 → expression ID 매핑 ---

# 실제 어떤 exp가 어떤 표정인지 몰라도 일단 이렇게 넣고
# 버튼 눌러보면서 "아 이게 happy네" 식으로 조정하면 됨.
EMOTION_EXPRESSION_ID = {
    "neutral": "exp_01",
    "happy": "exp_02",
    "sad": "exp_05",
}


class Live2DWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.current_emotion = "neutral"

        # idle 모션용 시간 변수
        self._last_time = None
        self._idle_t = 0.0

        # 60fps 근처로 계속 repaint
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(16)

    # OpenGL 컨텍스트 초기화
    def initializeGL(self):
        live2d.init()
        if live2d.LIVE2D_VERSION == 3:
            live2d.glewInit()

        here = Path(__file__).resolve().parent
        self.model = live2d.LAppModel()
        self.model.LoadModelJson(str(MODEL_DIRECTORY))
        self.model.Resize(self.width(), self.height())
        self.model.SetAutoBlinkEnable(True)
        self.model.SetAutoBreathEnable(True)

        self.apply_emotion(self.current_emotion)

        self._last_time = time.time()

    def resizeGL(self, w, h):
        if self.model:
            self.model.Resize(w, h)
    
    def _update_idle_motion(self, dt: float):
        if not self.model:
            return

        self._idle_t += dt

        angle_y = math.sin(self._idle_t * 1.2) * 10.0
        body_y = math.sin(self._idle_t * 0.8 + 1.0) * 5.0
        breath = (math.sin(self._idle_t * 0.9) + 1.0) * 0.5

        # 누적이 아니라 "현재 프레임의 값"으로 세팅하는 쪽이 안전해서 SetParameterValue 사용
        self.model.SetParameterValue(StandardParams.ParamAngleY, angle_y)
        self.model.SetParameterValue(StandardParams.ParamBodyAngleY, body_y)
        self.model.SetParameterValue(StandardParams.ParamBreath, breath)


    def paintGL(self):
        if not self.model:
            return

        now = time.time()
        if self._last_time is None:
            dt = 0.0
        else:
            dt = now - self._last_time
        self._last_time = now

        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # idle 모션 추가
        self._update_idle_motion(dt)

        # 모델 업데이트 + 그리기
        self.model.Update()
        self.model.Draw()

    def apply_emotion(self, emotion: str):
        """감정 이름(happy/sad/neutral)으로 expression 적용"""
        if not self.model:
            return

        exp_id = EMOTION_EXPRESSION_ID.get(emotion)
        if exp_id is None:
            print(f"[WARN] unknown emotion: {emotion}")
            return

        self.model.ResetExpression()
        self.model.SetExpression(exp_id)

        self.current_emotion = emotion
        self.update()

    def play_motion(self, group: str, no: int = 0, priority: int = 1):
        """model3.json 안에 정의된 motion 그룹/번호 실행"""
        if not self.model:
            return
        self.model.StartMotion(group, no, priority)
        self.update()


class MainWindow(QMainWindow):
    def __init__(self, controller: ChatController):
        super().__init__()
        self.setWindowTitle("Live2D + Chatbot UI Demo")
        self.controller=controller

        # 왼쪽: Live2D
        self.live2d_widget = Live2DWidget()

        # 오른쪽: 로그 + 감정 버튼들
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Please enter your input")
        self.input_box.returnPressed.connect(self.receive_input)
        
        btn_neutral = QPushButton("Neutral")
        btn_happy = QPushButton("Happy")
        btn_sad = QPushButton("Sad")
        btn_special = QPushButton("Special Motion")

        btn_neutral.clicked.connect(lambda: self.set_emotion("neutral"))
        btn_happy.clicked.connect(lambda: self.set_emotion("happy"))
        btn_sad.clicked.connect(lambda: self.set_emotion("sad"))

        # 예시: special 버튼 누르면 "special" 그룹 0번 모션 실행
        btn_special.clicked.connect(self.play_special_motion)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.log)
        right_layout.addWidget(self.input_box)
        right_layout.addWidget(btn_neutral)
        right_layout.addWidget(btn_happy)
        right_layout.addWidget(btn_sad)
        right_layout.addWidget(btn_special)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.addWidget(self.live2d_widget, 2)
        main_layout.addWidget(right_widget, 1)

        self.setCentralWidget(central)
        
    def receive_input(self):
        user_text = self.input_box.text()
        self.input_box.clear()
        self.log.append("User: "+ user_text)
        reply = self.controller.handle_user_message(text=user_text)
        self.log.append("AI BOT: " + reply)

    def set_emotion(self, emotion: str):
        #self.log.append(f"Set emotion → {emotion}")
        self.live2d_widget.apply_emotion(emotion)

        # 예시: happy/sad일 때 기본 모션도 하나 실행
        if emotion == "happy":
            self.live2d_widget.play_motion("", 0)
        elif emotion == "sad":
            self.live2d_widget.play_motion("", 1)
        elif emotion == "neutral":
            self.live2d_widget.play_motion("Idle", 0)

    def play_special_motion(self):
        self.log.append("Play special motion")
        self.live2d_widget.play_motion("", 4)


class ChatUI():

    def __init__(self, controller: ChatController):
        app = QApplication(sys.argv)
        win = MainWindow(controller)
        win.resize(1200, 700)
        win.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
