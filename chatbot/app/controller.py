
from chatbot.core.chat_service import ChatService

class ChatController:
    def __init__(self, service: ChatService):
        self.service = service
        
    def handle_user_message(self, text:str) -> str:
        
        #유저 입력 검증(ex 빈 입력)
        #오류 처리 등
        result = self.service.run_turn(text)
        return result.reply
    
    def shutdown(self) -> None:
        """Called when UI exits so the service can clean resources."""
        self.service.close_session()