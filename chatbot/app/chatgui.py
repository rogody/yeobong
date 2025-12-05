#from pathlib import Path
#import math
#import time
#import os
import sys
import os
from pathlib import Path

#from chatbot.modules.llm_model import LLModel
from chatbot.core.chat_service import ChatService
from .live2dwidget import Live2DWidget
from .chat_thread import ChatWorker
from chatbot.core.types import ChatResult
from .ply_render import WebViewer

from OpenGL.GL import (
    glClearColor,
    glClear,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
)

import live2d.v3 as live2d
from live2d.v3 import StandardParams

from PySide6.QtCore import QThread, Signal, Slot
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
from PySide6.QtGui import QColor
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# 프로젝트 루트 및 리소스 경로
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES_DIR = PROJECT_ROOT / "Resources"
BG_PLY = RESOURCES_DIR / "projply" / "scene.compressed.ply"
ACTOR_PLY = RESOURCES_DIR / "projply" / "jsw.ply"  # 없으면 배경만 로드
# 감정별 PLY는 Resources/projply/<emotion>.ply 로 가정
EMOTION_DIR = RESOURCES_DIR / "projply"
# 모든 감정/배경이 들어 있는 ssproj (배경, 카메라 포함) - 있으면 사용, 없으면 PLY 로드
ALL_EMO_SSPROJ = RESOURCES_DIR / "projply" / "all_emotions.ssproj"


class MainWindow(QMainWindow):
    def __init__(self, service: ChatService):
        super().__init__()
        live2d.init()
        self.live2d_widget = Live2DWidget()
        self.set_ui()
        # ssproj를 사용할 것이므로 auto_load=False
        self.gs_widget = WebViewer(auto_load=False)
        self.chat_service = service
        self.model_name = "Ai Bot"
        self.mode = "2d"  # 2d | 3d
        # 감정 라벨 -> ply 파일명 매핑 (없으면 neutral로 대체)
        self.emotion_map = {
            "happy": EMOTION_DIR / "happy.ply",
            "sad": EMOTION_DIR / "sad.ply",
            "surprise": EMOTION_DIR / "surprise.ply",
            "disgusted": EMOTION_DIR / "disgusted.ply",
            "upset": EMOTION_DIR / "upset.ply",
            # neutral 대체: 기본 배우 PLY (없으면 건너뜀)
            "neutral": ACTOR_PLY,
        }
        # 감정 -> 파일명(basename) 매핑 (ssproj 내에서 visible 토글용)
        self.emotion_basenames = {k: v.name for k, v in self.emotion_map.items() if v}

    def set_ui(self):
        self.setWindowTitle("AI chat bot ")
        self.resize(600, 500)
        #self.setStyleSheet("background-color: black;")
        
        self.epsilon_button = QPushButton("EPSILON")
        self.gs_button = QPushButton("3D MODE")
        #self.huohuo_button = QPushButton("HUOHUO")
        #elf.frieren_button = QPushButton("FRIEREN")
        self.delete_button = QPushButton("DELETE")
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.epsilon_button)
        model_layout.addWidget(self.gs_button)
        #model_layout.addWidget(self.huohuo_button)
        #model_layout.addWidget(self.frieren_button)
        model_layout.addWidget(self.delete_button)
        model_widget = QWidget()
        model_widget.setLayout(model_layout)
        
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Enter your text")
        self.line_edit.returnPressed.connect(self.input_pressed)
        
        self.enter_button = QPushButton("Enter")
        self.enter_button.clicked.connect(self.input_pressed)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.line_edit)
        input_layout.addWidget(self.enter_button)
        input_widget = QWidget()
        input_widget.setLayout(input_layout)
        
        chatbot_layout = QVBoxLayout()
        chatbot_layout.addWidget(model_widget)
        chatbot_layout.addWidget(self.result_display)
        chatbot_layout.addWidget(input_widget)
        
        chatbot_widget = QWidget()
        chatbot_widget.setLayout(chatbot_layout)
        
        self.setCentralWidget(chatbot_widget)
        
        self.epsilon_button.clicked.connect(self.show_epsilon)
        self.gs_button.clicked.connect(self.show_gs)
        #self.huohuo_button.clicked.connect(self.show_haru)
        #self.frieren_button.clicked.connect(self.show_frieren)
        self.delete_button.clicked.connect(self.delete_model)
        
    
        
    def input_pressed(self):
        text = self.line_edit.text()
        if not text:
            return
        self.line_edit.clear()
        self.result_display.append("User: " + text)  
        self.llm_thread = ChatWorker(self.chat_service, text)
        self.enter_button.setEnabled(False)
        self.line_edit.setEnabled(False)
        self.llm_thread.llm_replied.connect(self.llm_content)
        self.llm_thread.start()
        
    @Slot(ChatResult)
    def llm_content(self, llm_response):
        self.result_display.append(self.model_name + ": " + llm_response.reply)
        self.enter_button.setEnabled(True)
        self.line_edit.setEnabled(True)
        self.live2d_widget.set_motion(llm_response.emotion)
        if self.mode == "3d" and llm_response.emotion:
            self._update_3d_scene(llm_response.emotion)


    def show_gs(self):
        # 3D 모드 전환 및 초기 씬 로드
        self.mode = "3d"
        if ALL_EMO_SSPROJ.exists():
            self.gs_widget.load_scene([str(ALL_EMO_SSPROJ)])
        else:
            # ssproj가 없으면 기본 배경+중립 배우 로드
            self.gs_widget.load_scene([str(BG_PLY), str(ACTOR_PLY)])
        # 초기 감정 상태 반영
        self._update_3d_scene("neutral")
        self.gs_widget.show()

    def show_epsilon(self):
        self.model_name = "EPSILON"
        self.mode = "2d"
        live2d.dispose()
        live2d.init()
        self.show_live2d("epsilon")
    
    '''
    def show_haru(self):
        live2d.dispose()
        live2d.init()
        self.show_live2d("huohuo")
        
    def show_frieren(self):
        live2d.dispose()
        live2d.init()
        self.show_live2d("frieren")
    '''
    def delete_model(self):
        self.model_name = "Ai Bot"
        self.mode = "2d"
        live2d.dispose()
        self.live2d_widget.close()
        self.gs_widget.close()

    def show_live2d(self, name:str):
        self.live2d_widget.set_model(name)
        self.live2d_widget.show()

    def _update_3d_scene(self, emotion_label: str):
        """
        현재 감정 라벨을 받아 3D 씬을 재로딩한다.
        ssproj를 사용하는 경우: 배경/카메라는 ssproj에 있으므로 감정 PLY만 visible 토글.
        ssproj가 없으면 기존 방식으로 배경 + 배우 + 감정별 PLY 로드.
        """
        if ALL_EMO_SSPROJ.exists():
            # ssproj 내에서 visible만 토글
            self.gs_widget.set_visible_emotion(emotion_label, self.emotion_basenames)
        else:
            # fallback: 배경 + 배우 + 감정별 PLY 로드
            paths = [str(BG_PLY), str(ACTOR_PLY)]
            emo_path = self.emotion_map.get(emotion_label.lower())
            if emo_path is None:
                emo_path = self.emotion_map.get("neutral")
            if emo_path and emo_path.exists():
                paths.append(str(emo_path))
            self.gs_widget.load_scene(paths)
        
'''
if __name__ == "__main__":
    
    live2d.init()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
    
    live2d.dispose()
'''

    
