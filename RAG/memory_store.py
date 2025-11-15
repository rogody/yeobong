# memory_store.py
from __future__ import annotations

import ulid  # uuid helper
from typing import List, Tuple

from RAG.db_client import DBClient
from RAG.embedding_client import EmbeddingClient
from RAG.text_chunker import TextChunk, chunk_text


class MemoryStore:
    def __init__(
        self,
        db: DBClient,
        emb_client: EmbeddingClient,
        chunk_token_size: int = 250,
        chunk_overlap_ratio: float = 0.2,
    ):
        self.db = db
        self.emb_client = emb_client
        self.chunk_token_size = chunk_token_size
        self.chunk_overlap_ratio = chunk_overlap_ratio

    def _new_id(self) -> str:
        return str(ulid.new())  # CHAR(26) friendly

    # Conversation helpers ---------------------------------
    def create_conversation(self, title: str | None = None) -> str:
        conv_id = self._new_id()
        self.db.execute(
            """
            INSERT INTO conversations (conv_id, title)
            VALUES (%s, %s)
            """,
            (conv_id, title),
        )
        return conv_id

    def delete_conversation(self, conv_id: str) -> None:
        """Remove a conversation; cascades clear messages/chunks/embeddings."""
        if not conv_id:
            return
        self.db.execute(
            """
            DELETE FROM conversations
            WHERE conv_id = %s
            """,
            (conv_id,),
        )

    # Message & embedding logic -------------------------------------------
    def insert_message(
        self,
        conv_id: str,
        author_kind: str,
        content: str,
    ) -> str:
        msg_id = self._new_id()
        row = self.db.fetchone(
            "SELECT COALESCE(MAX(turn_index), 0) AS mx "
            "FROM messages WHERE conv_id=%s",
            (conv_id,),
        )
        current_max = row["mx"] if row else 0
        turn_index = current_max + 1

        self.db.execute(
            """
            INSERT INTO messages
              (msg_id, conv_id, author_kind,
               turn_index, content_raw)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (msg_id, conv_id, author_kind, turn_index, content),
        )
        return msg_id

    def _message_chunks(self, content: str) -> List[TextChunk]:
        return chunk_text(
            content,
            chunk_size=self.chunk_token_size,
            overlap_ratio=self.chunk_overlap_ratio,
        )

    def insert_message_chunks(
        self,
        conv_id: str,
        msg_id: str,
        content: str,
    ) -> List[Tuple[int, TextChunk]]:
        chunks = self._message_chunks(content)
        chunk_records: List[Tuple[int, TextChunk]] = []
        for chunk in chunks:
            chunk_id = self.db.execute(
                """
                INSERT INTO message_chunks
                  (conv_id, msg_id, ord, token_start, token_end, chunk_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    conv_id,
                    msg_id,
                    chunk.ord,
                    chunk.token_start,
                    chunk.token_end,
                    chunk.text,
                ),
            )
            chunk_records.append((chunk_id, chunk))
        return chunk_records

    def insert_chunk_embedding(self, chunk_id: int, chunk_text_value: str):
        vec = self.emb_client.encode(chunk_text_value)
        blob = vec.tobytes()
        self.db.execute(
            """
            INSERT INTO chunk_embeddings
              (chunk_id, model, dim, vector_blob)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              vector_blob=VALUES(vector_blob),
              updated_at=CURRENT_TIMESTAMP
            """,
            (chunk_id, self.emb_client.model_name, self.emb_client.dim, blob),
        )

    def save_with_embedding(
        self,
        conv_id: str,
        author_kind: str,
        content: str,
    ):
        msg_id = self.insert_message(conv_id, author_kind, content)
        chunk_records = self.insert_message_chunks(conv_id, msg_id, content)
        for chunk_id, chunk in chunk_records:
            self.insert_chunk_embedding(chunk_id, chunk.text)
        return msg_id, [chunk_id for chunk_id, _ in chunk_records]
