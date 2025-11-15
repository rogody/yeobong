import os

from chatbot.modules.llm_model import LLModel
from chatbot.app.ui import ChatUI
from chatbot.app.controller import ChatController
from chatbot.core.chat_service import ChatService
from chatbot.core.prompt_builder import PromptBuilder
from RAG.db_client import DBClient
from RAG.embedding_client import EmbeddingClient
from RAG.memory_store import MemoryStore
from RAG.memory_retriever import MemoryRetriever


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def main():
    # modules의 각종 객체들 생성해서 chatserivce의 init으로 넘김
    # chatservice는 chatcontroller의 init으로 넘김
    # chatcontroller는 chatui의 init으로 넘김

    model_name = "WeiboAI/VibeThinker-1.5B"

    chunk_size = _int_env("RAG_CHUNK_SIZE", 250)
    chunk_overlap = _float_env("RAG_CHUNK_OVERLAP", 0.2)
    retrieval_top_k = _int_env("RAG_RETRIEVE_TOP_K", 4)

    # 1) LLM 로드 (조금 시간이 걸릴 수 있음)
    llm_client = LLModel(model_name)

    db_client = None
    memory_store = None
    memory_retriever = None
    embedding_client = None
    try:
        db_client = DBClient()
        embedding_client = EmbeddingClient()
        memory_store = MemoryStore(
            db_client,
            embedding_client,
            chunk_token_size=chunk_size,
            chunk_overlap_ratio=chunk_overlap,
        )
        memory_retriever = MemoryRetriever(db_client, embedding_client)
    except Exception as exc:
        print(f"[WARN] Failed to initialize RAG components: {exc}")
        memory_store = None
        memory_retriever = None

    prompt_builder = PromptBuilder()
    chat_service = ChatService(
        llm_client,
        prompt_builder,
        memory_store=memory_store,
        memory_retriever=memory_retriever,
        retrieval_top_k=retrieval_top_k,
    )
    chat_controller = ChatController(chat_service)

    # 3) UI 실행
    ui = ChatUI(chat_controller)
    try:
        ui.run()
    finally:
        if db_client:
            db_client.close()


if __name__ == "__main__":
    main()
