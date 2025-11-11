from chatbot.modules.llm_model import LLModel
from chatbot.app.ui import ChatUI
from chatbot.app.controller import ChatController
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
import customtkinter as ctk


def main():
    # modules의 각종 객체들 생성해서 chatserivce의 init으로 넘김
    # chatservice는 chatcontroller의 init으로 넘김
    # chatcontroller는 chatui의 init으로 넘김

    model_name = "WeiboAI/VibeThinker-1.5B"

    # 1) LLM 로드 (조금 시간 걸릴 수 있음)
    llm_client = LLModel(model_name)

    prompt_builder = PromptBuilder()
    chat_service = ChatService(llm_client, prompt_builder)
    chat_controller = ChatController(chat_service)

    # 3) UI 실행
    ui = ChatUI(chat_controller)
    ui.run()


if __name__ == "__main__":
    main()
