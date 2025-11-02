from sentence_transformers import SentenceTransformer
from packages.core.ports.embedder import EmbedderPort

class SBertEmbedder(EmbedderPort):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    def embed(self, texts):
        return self.model.encode(list(texts), normalize_embeddings=True).tolist()
