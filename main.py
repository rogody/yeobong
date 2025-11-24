from chatbot.modules.llm_model import LLModel
from chatbot.app.ui import ChatUI
from chatbot.app.controller import ChatController
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
from RAG.factory import init_rag_components


def main():
    # modules의 각종 객체들 생성해서 chatserivce의 init으로 넘김
    # chatservice는 chatcontroller의 init으로 넘김
    # chatcontroller는 chatui의 init으로 넘김

    model_name = "Qwen/Qwen3-1.7B"

    # 1) LLM 로드 (조금 시간 걸릴 수 있음)
    llm_client = LLModel(model_name)
    rag = init_rag_components()

    prompt_builder = PromptBuilder()
    chat_service = ChatService(
        llm_client,
        prompt_builder,
        memory_store=rag.memory_store,
        memory_retriever=rag.memory_retriever,
        retrieval_top_k=rag.settings.retrieval_top_k,
    )
    chat_controller = ChatController(chat_service)
    # 3) UI 실행
    ui = ChatUI(chat_controller)
    try:
        ui.run()
    finally:
        rag.close()


if __name__ == "__main__":
    main()
