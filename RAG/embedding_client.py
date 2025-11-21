# embedding_client.py
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingClient:
    def __init__(self, model_name="BAAI/bge-large-en-v1.5"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str) -> np.ndarray:
        emb = self.model.encode([text], normalize_embeddings=True)[0]
        return emb.astype("float32")
