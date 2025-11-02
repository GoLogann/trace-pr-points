import os, uuid
from typing import Sequence
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct
from packages.core.ports.vector_repo import VectorRepoPort, VectorDoc
from packages.core.ports.embedder import EmbedderPort

class QdrantRepo(VectorRepoPort):
    def __init__(self, embedder: EmbedderPort, collection: str | None = None):
        host = os.getenv("QDRANT_HOST","localhost")
        port = int(os.getenv("QDRANT_PORT","6333"))
        self.collection = collection or os.getenv("QDRANT_COLLECTION","normativos")
        self.client = QdrantClient(host=host, port=port)
        self.embedder = embedder
        self._ensure_collection()

    def _ensure_collection(self):
        # 384 para MiniLM; ajuste se trocar embedder
        size = 384
        self.client.recreate_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE)
        )

    def upsert(self, docs: Sequence[VectorDoc]) -> None:
        vectors = self.embedder.embed([d["text"] for d in docs])
        points = [PointStruct(id=d["id"], vector=vectors[i], payload=d["metadata"] | {"text": d["text"]}) for i,d in enumerate(docs)]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query: str, filters: dict | None = None, k: int = 4) -> list[VectorDoc]:
        qvec = self.embedder.embed([query])[0]
        f = None
        if filters:
            conds = [FieldCondition(key=k, match=MatchValue(value=v)) for k,v in filters.items()]
            f = Filter(must=conds)
        r = self.client.search(self.collection, query_vector=qvec, limit=k, query_filter=f)
        return [{"id": str(p.id), "text": p.payload.get("text",""), "metadata": p.payload} for p in r]
