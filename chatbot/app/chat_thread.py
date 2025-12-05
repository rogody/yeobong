from __future__ import annotations
from PySide6.QtCore import QThread, Signal
from chatbot.core.chat_service import ChatService

from chatbot.core.chat_service import ChatService
from chatbot.core.types import ChatResult

class ChatWorker(QThread):
    llm_replied  = Signal(ChatResult)

    def __init__(self, service: ChatService, text:str):
        super().__init__()
        self.service = service
        self.user_text = text
        
    def run(self) -> str:
        result = self.service.run_turn(self.user_text)
        self.llm_replied.emit(result)
        
