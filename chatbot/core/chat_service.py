"""LLM 서비스 계층: 프롬프트 생성 -> 모델 호출 -> 결과/메모리 연동"""

from __future__ import annotations

import logging
import re
from typing import Optional, TYPE_CHECKING

from chatbot.modules.llm_model import LLModel
from chatbot.core.types import ChatResult
from chatbot.core.prompt_builder import PromptBuilder

if TYPE_CHECKING:  # type hints 전용, 실제 런타임 의존성은 주입
    from RAG.memory_store import MemoryStore
    from RAG.memory_retriever import MemoryRetriever


class ChatService:
    _think_pattern = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)

    def __init__(
        self,
        llm: LLModel,
        prompt_builder: PromptBuilder,
        memory_store: Optional["MemoryStore"] = None,
        memory_retriever: Optional["MemoryRetriever"] = None,
        retrieval_top_k: int = 4,
    ):
        self.llm = llm
        self.pb = prompt_builder
        self.memory_store = memory_store
        self.memory_retriever = memory_retriever
        self.retrieval_top_k = retrieval_top_k

        self.conv_id: Optional[str] = None
        if self.memory_store:
            self._initialize_conversation()

    def _initialize_conversation(self) -> None:
        try:
            self.conv_id = self.memory_store.create_conversation(title="Yeobong Session")
        except Exception as exc:
            logging.warning("Failed to initialize RAG memory conversation: %s", exc)
            self.memory_store = None
            self.memory_retriever = None

    def run_turn(self, user_input: str) -> ChatResult:
        context_text = self._build_context(user_input)
        prompt = self.pb.build(user_input, context=context_text)
        reply = self.llm.generate(prompt)

        self._persist_message("user", user_input)
        self._persist_message("assistant", reply)

        return ChatResult(reply=reply)

    def _build_context(self, user_input: str) -> Optional[str]:
        if not self.memory_retriever:
            return None
        try:
            chunks = self.memory_retriever.search(user_input, top_k=self.retrieval_top_k)
        except Exception as exc:
            logging.warning("Memory retrieval failed: %s", exc)
            return None
        if not chunks:
            return None

        formatted = []
        for row in chunks:
            snippet = row.get("chunk_text", "").strip()
            if not snippet:
                continue
            prefix = f"conv={row.get('conv_id')} msg={row.get('msg_id')} ord={row.get('ord')}"
            formatted.append(f"[{prefix}] {snippet}")
        return "\n".join(formatted) if formatted else None

    def _persist_message(self, author_kind: str, content: str) -> None:
        if not self.memory_store or not self.conv_id:
            return
        clean = self._strip_think(content)
        if not clean:
            return
        try:
            self.memory_store.save_with_embedding(
                conv_id=self.conv_id,
                author_kind=author_kind,
                content=clean,
            )
        except Exception as exc:
            logging.warning("Failed to persist %s message: %s", author_kind, exc)

    def close_session(self) -> None:
        if not self.memory_store or not self.conv_id:
            return
        try:
            self.memory_store.delete_conversation(self.conv_id)
        except Exception as exc:
            logging.warning("Failed to delete conversation %s: %s", self.conv_id, exc)
        finally:
            self.conv_id = None

    def _strip_think(self, text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = self._think_pattern.sub("", text)
        return cleaned.strip()
