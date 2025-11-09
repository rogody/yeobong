from chatbot.infra.llm_model import LLModel
from chatbot.ui.chatui import ChatUI, SimpleLLMBackend
import customtkinter as ctk


def main():
    # 1) LLM 로드 (조금 시간 걸릴 수 있음)
    llm_client = LLModel()

    # 2) 간단 백엔드 생성
    backend = SimpleLLMBackend(llm_client)

    # 3) UI 실행
    ui = ChatUI(backend)
    ui.run()

if __name__ == "__main__":
    main()
  