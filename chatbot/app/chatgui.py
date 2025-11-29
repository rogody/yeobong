#from pathlib import Path
#import math
#import time
#import os
import sys

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


class MainWindow(QMainWindow):
    def __init__(self, service: ChatService):
        super().__init__()
        live2d.init()
        self.live2d_widget = Live2DWidget()
        self.set_ui()
        self.gs_widget = WebViewer()
        self.chat_service = service
        self.model_name = "Ai Bot"

    def set_ui(self):
        self.setWindowTitle("AI chat bot ")
        self.resize(600, 500)
        #self.setStyleSheet("background-color: black;")
        
        self.epsilon_button = QPushButton("EPSILON")
        self.gs_button = QPushButton("3DGS")
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


    def show_gs(self):
        self.gs_widget.show()

    def show_epsilon(self):
        self.model_name = "EPSILON"
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
        live2d.dispose()
        self.live2d_widget.close()
        self.gs_widget.close()

    def show_live2d(self, name:str):
        self.live2d_widget.set_model(name)
        self.live2d_widget.show()
        
'''
if __name__ == "__main__":
    
    live2d.init()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
    
    live2d.dispose()
'''

    