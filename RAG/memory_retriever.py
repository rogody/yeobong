# memory_retriever.py
import numpy as np
from db_client import DBClient
from embedding_client import EmbeddingClient

class MemoryRetriever:
    def __init__(self, db: DBClient, emb_client: EmbeddingClient):
        self.db = db
        self.emb_client = emb_client

    def _load_candidates(self, limit=500):
        cur = self.db.execute(
            """
            SELECT m.msg_id, m.content_raw, e.vector_blob
            FROM message_embeddings e
            JOIN messages m ON m.msg_id = e.msg_id
            WHERE e.model = %s
            ORDER BY m.created_at DESC
            LIMIT %s
            """,
            (self.emb_client.model_name, limit)
        )
        rows = cur.fetchall()
        for r in rows:
            vec = np.frombuffer(r["vector_blob"], dtype="float32")
            r["vector"] = vec
        return rows

    def search(self, query: str, top_k=5):
        q = self.emb_client.encode(query)
        cands = self._load_candidates()

        # 코사인 유사도
        sims = []
        for r in cands:
            v = r["vector"]
            score = float(np.dot(q, v))   # 둘 다 normalize 되어있다고 가정
            sims.append((score, r))

        sims.sort(key=lambda x: x[0], reverse=True)
        return [r for score, r in sims[:top_k]]
