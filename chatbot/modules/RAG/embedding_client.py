# embedding_client.py
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from chatbot.app import paths

embedding_model_path = str(paths.EMBEDDING_DIR)
DEFAULT_MODEL_ID = "BAAI/bge-large-en-v1.5"

class EmbeddingClient:
    def __init__(self, model_name: str = DEFAULT_MODEL_ID):
        self.model_name = model_name
        cache_folder = embedding_model_path
        os.makedirs(cache_folder, exist_ok=True)

        try:
            self.model = SentenceTransformer(self.model_name, cache_folder=cache_folder)
        except OSError:
            print("no embedding model found locally. download is needed.")
            self.model = SentenceTransformer(DEFAULT_MODEL_ID, cache_folder=cache_folder)
        
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str) -> np.ndarray:
        emb = self.model.encode([text], normalize_embeddings=True)[0]
        return emb.astype("float32")
