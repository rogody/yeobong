# memory_retriever.py
import numpy as np
from .db_client import DBClient
from .embedding_client import EmbeddingClient


class MemoryRetriever:
    def __init__(self, db: DBClient, emb_client: EmbeddingClient):
        self.db = db
        self.emb_client = emb_client

    def _load_candidates(self, limit: int = 500):
        rows = self.db.fetchall(
            """
            SELECT mc.chunk_id, mc.conv_id, mc.msg_id, mc.chunk_text,
                   mc.ord, mc.token_start, mc.token_end,
                   ce.vector_blob
            FROM chunk_embeddings ce
            JOIN message_chunks mc ON mc.chunk_id = ce.chunk_id
            WHERE ce.model = %s
            ORDER BY mc.created_at DESC
            LIMIT %s
            """,
            (self.emb_client.model_name, limit),
        )
        for row in rows:
            vec = np.frombuffer(row["vector_blob"], dtype="float32")
            row["vector"] = vec
        return rows

    def search(self, query: str, top_k: int = 3):
        query_vec = self.emb_client.encode(query)
        candidates = self._load_candidates()

        scores = []
        for row in candidates:
            chunk_vec = row["vector"]
            score = float(np.dot(query_vec, chunk_vec))
            scores.append((score, row))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [row for score, row in scores[:top_k]]
