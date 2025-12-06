import os
from dataclasses import dataclass
from typing import Optional

from .db_client import DBClient
from .embedding_client import EmbeddingClient
from .memory_store import MemoryStore
from .memory_retriever import MemoryRetriever
from chatbot.app import paths


EMBEDDING_PATH = paths.BASE_DIR / "model" / "embedding"
embedding_model_path = str(EMBEDDING_PATH)

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


@dataclass
class RAGSettings:
    chunk_size: int = 150
    chunk_overlap: float = 0.2
    retrieval_top_k: int = 3


@dataclass
class RAGComponents:
    db_client: Optional[DBClient]
    embedding_client: Optional[EmbeddingClient]
    memory_store: Optional[MemoryStore]
    memory_retriever: Optional[MemoryRetriever]
    settings: RAGSettings

    def close(self) -> None:
        if self.db_client:
            self.db_client.close()


def load_rag_settings() -> RAGSettings:
    return RAGSettings(
        chunk_size=_int_env("RAG_CHUNK_SIZE", 150),
        chunk_overlap=_float_env("RAG_CHUNK_OVERLAP", 0.2),
        retrieval_top_k=_int_env("RAG_RETRIEVE_TOP_K", 3),
    )


def init_rag_components() -> RAGComponents:
    settings = load_rag_settings()
    db_client: Optional[DBClient] = None
    embedding_client: Optional[EmbeddingClient] = None
    memory_store: Optional[MemoryStore] = None
    memory_retriever: Optional[MemoryRetriever] = None
    try:
        db_client = DBClient()
        if embedding_model_path:
            embedding_client = EmbeddingClient(model_name=embedding_model_path)
        else:
            embedding_client = EmbeddingClient()
        memory_store = MemoryStore(
            db_client,
            embedding_client,
            chunk_token_size=settings.chunk_size,
            chunk_overlap_ratio=settings.chunk_overlap,
        )
        memory_retriever = MemoryRetriever(db_client, embedding_client)
    except Exception as exc:
        print(f"[WARN] Failed to initialize RAG components: {exc}")
        memory_store = None
        memory_retriever = None
    return RAGComponents(
        db_client=db_client,
        embedding_client=embedding_client,
        memory_store=memory_store,
        memory_retriever=memory_retriever,
        settings=settings,
    )
