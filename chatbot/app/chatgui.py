
from pathlib import Path

from chatbot.core.chat_service import ChatService
from .live2dwidget import Live2DWidget
from .chat_thread import ChatWorker
from chatbot.core.types import ChatResult
from .ply_render import WebViewer

import live2d.v3 as live2d

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLineEdit,
)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES_DIR = PROJECT_ROOT / "Resources"
PROJPLY_DIR = RESOURCES_DIR / "projply"
BG_PLY = PROJPLY_DIR / "youngsin.ply"  # fixed background
ACTOR_PLY = PROJPLY_DIR / "jsw.ply"    # neutral actor


class MainWindow(QMainWindow):
    def __init__(self, service: ChatService):
        super().__init__()
        live2d.init()
        self.live2d_widget = Live2DWidget()
        self.set_ui()
        # auto_load=False: we will specify PLYs manually
        self.gs_widget = WebViewer(auto_load=False)
        self.chat_service = service
        self.model_name = "Ai Bot"
        self.mode = "2d"  # 2d | 3d
        self._overlay_demo_shown = False
        # Emotion -> PLY path
        self.emotion_map = {
            "happy": PROJPLY_DIR / "happy.ply",
            "joy": PROJPLY_DIR / "happy.ply",  # emotion 모델 출력 보정
            "sad": PROJPLY_DIR / "sad.ply",
            "surprise": PROJPLY_DIR / "surprise.ply",
            "disgusted": PROJPLY_DIR / "disgusted.ply",
            "disgust": PROJPLY_DIR / "disgusted.ply",
            "anger": PROJPLY_DIR / "upset.ply",
            "angry": PROJPLY_DIR / "upset.ply",
            "fear": PROJPLY_DIR / "upset.ply",
            "upset": PROJPLY_DIR / "upset.ply",
            "neutral": ACTOR_PLY,
        }
        self._gs_loaded = False

    def set_ui(self):
        self.setWindowTitle("AI chat bot ")
        self.resize(600, 500)

        self.epsilon_button = QPushButton("EPSILON")
        self.gs_button = QPushButton("3D MODE")
        self.delete_button = QPushButton("DELETE")

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.epsilon_button)
        model_layout.addWidget(self.gs_button)
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
        if self.mode == "3d":
            emotion = self._normalize_emotion(llm_response.emotion)
            self._update_3d_scene(emotion)

    def show_gs(self):
        self.mode = "3d"
        if not self._gs_loaded:
            preload_paths = {BG_PLY, ACTOR_PLY}
            preload_paths.update(self.emotion_map.values())
            existing = [str(p) for p in preload_paths if p.exists()]
            self.gs_widget.preload_scene(
                existing,
                initial_visible=[BG_PLY.name, ACTOR_PLY.name],
                always_visible=[BG_PLY.name],
                fallback_name=ACTOR_PLY.name,
            )
            self._gs_loaded = True
        else:
            self.gs_widget.set_visibility(
                [BG_PLY.name, ACTOR_PLY.name],
                always_visible=[BG_PLY.name],
                fallback_name=ACTOR_PLY.name,
            )
        # 최초 진입만 오버레이 유지, 이후에는 끈 상태로 시작
        if self._overlay_demo_shown:
            self.gs_widget.set_overlay(False)
        else:
            self._overlay_demo_shown = True
        # 배경/그리드 조정
        self.gs_widget.set_grid(False)
        self.gs_widget.set_background(0.97, 0.97, 0.97, 1.0)
        self.gs_widget.show()

    def show_epsilon(self):
        self.mode = "2d"
        live2d.dispose()
        live2d.init()
        self.show_live2d("epsilon")

    def delete_model(self):
        self.mode = "2d"
        live2d.dispose()
        self.live2d_widget.close()
        self.gs_widget.close()

    def closeEvent(self, event):
        """
        창 닫을 때 대화 로그(DB) 정리.
        """
        try:
            self.chat_service.close_session()
        except Exception:
            pass
        super().closeEvent(event)

    def show_live2d(self, name: str):
        self.live2d_widget.set_model(name)
        self.live2d_widget.show()

    def _update_3d_scene(self, emotion_label: str):
        """
        배경은 유지하고 감정 PLY만 토글한다.
        """
        emo_path = self.emotion_map.get(emotion_label.lower()) or self.emotion_map.get("neutral")
        target_files = [BG_PLY.name]
        fallback = None
        if emo_path and emo_path.exists():
            target_files.append(emo_path.name)
        else:
            target_files.append(ACTOR_PLY.name)
            fallback = ACTOR_PLY.name
        self.gs_widget.set_visibility(
            target_files,
            always_visible=[BG_PLY.name],
            fallback_name=fallback,
        )
        # 감정 전환 이후에는 Gaussian overlay 끄기
        self.gs_widget.set_overlay(False)

    def _normalize_emotion(self, label: str | None) -> str:
        """
        모델 출력과 파일명 매핑을 보정해 렌더링 실패를 줄인다.
        """
        if not label:
            return "neutral"
        l = label.lower()
        # 직접 매핑이 있으면 그대로 사용
        if l in self.emotion_map:
            return l
        # 추가 보정 규칙
        if "joy" in l:
            return "happy"
        if "ang" in l:
            return "upset"
        if "fear" in l:
            return "upset"
        if "disgust" in l:
            return "disgusted"
        if "surpris" in l:
            return "surprise"
        if "sad" in l:
            return "sad"
        return "neutral"

