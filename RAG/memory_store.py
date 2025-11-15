# memory_store.py
import ulid       # 또는 uuid
import numpy as np
from db_client import DBClient
from embedding_client import EmbeddingClient

class MemoryStore:
    def __init__(self, db: DBClient, emb_client: EmbeddingClient):
        self.db = db
        self.emb_client = emb_client

    def _new_id(self) -> str:
        return str(ulid.new())  # CHAR(26)과 궁합 맞음

    def insert_message(self, conv_id: str, author_kind: str, content: str,
                       author_id: str | None = None) -> str:
        msg_id = self._new_id()
        # turn_index는 간단히 max+1로 계산 (실서비스면 race cond. 주의)
        cur = self.db.execute(
            "SELECT COALESCE(MAX(turn_index), 0) AS mx "
            "FROM messages WHERE conv_id=%s",
            (conv_id,)
        )
        row = cur.fetchone()
        turn_index = row["mx"] + 1

        self.db.execute(
            """
            INSERT INTO messages
              (msg_id, conv_id, author_id, author_kind,
               turn_index, content_raw)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (msg_id, conv_id, author_id, author_kind, turn_index, content)
        )
        return msg_id

    def insert_message_embedding(self, msg_id: str, content: str):
        vec = self.emb_client.encode(content)
        blob = vec.tobytes()
        self.db.execute(
            """
            INSERT INTO message_embeddings
              (msg_id, model, dim, vector_blob)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              vector_blob=VALUES(vector_blob),
              updated_at=CURRENT_TIMESTAMP
            """,
            (msg_id, self.emb_client.model_name, self.emb_client.dim, blob)
        )

    def save_with_embedding(self, conv_id: str, author_kind: str,
                            content: str, author_id: str | None = None):
        msg_id = self.insert_message(conv_id, author_kind, content, author_id)
        self.insert_message_embedding(msg_id, content)
        return msg_id
