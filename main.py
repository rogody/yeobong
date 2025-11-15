from chatbot.modules.llm_model import LLModel
from chatbot.app.ui import ChatUI
from chatbot.app.controller import ChatController
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
from RAG.factory import init_rag_components


def main():
    model_name = "Qwen/Qwen3-1.7B"

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

    ui = ChatUI(chat_controller)
    try:
        ui.run()
    finally:
        rag.close()


if __name__ == "__main__":
    main()
