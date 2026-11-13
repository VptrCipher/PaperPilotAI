import os
from threading import Lock
from uuid import uuid4

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
from chromadb.config import Settings

from config import EMBEDDING_DIR
from core.pdf_processor import Paper

ENCODE_LOCK = Lock()


def load_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        str(EMBEDDING_DIR), device="cpu", local_files_only=True
    )


class PaperIndex:
    """One active collection per UI session, held in Chroma's in-memory client."""

    def __init__(self, embedder):
        self.embedder = embedder
        self.client = chromadb.EphemeralClient(Settings(anonymized_telemetry=False))
        self.paper = None
        self.collection = None

    def clear(self):
        if self.collection is not None:
            self.client.delete_collection(self.collection.name)
        self.paper = None
        self.collection = None

    def _vectors(self, texts):
        with ENCODE_LOCK:
            return self.embedder.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            ).tolist()

    def index(self, paper: Paper) -> bool:
        if self.paper and self.paper.document_id == paper.document_id:
            return False
        self.clear()
        collection = self.client.create_collection(
            name=f"paper-{uuid4().hex}", configuration={"hnsw": {"space": "cosine"}}
        )
        try:
            for start in range(0, len(paper.chunks), 64):
                batch = paper.chunks[start:start + 64]
                texts = [chunk["text"] for chunk in batch]
                collection.add(
                    ids=[chunk["id"] for chunk in batch],
                    documents=texts,
                    embeddings=self._vectors(texts),
                    metadatas=[
                        {key: value for key, value in chunk.items() if key not in {"text", "id"}}
                        for chunk in batch
                    ],
                )
        except Exception:
            self.client.delete_collection(collection.name)
            raise
        self.paper = paper
        self.collection = collection
        return True

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if self.collection is None:
            raise ValueError("Index a PDF before searching.")
        results = self.collection.query(
            query_embeddings=self._vectors([query]),
            n_results=min(limit, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        return [
            dict(meta, id=chunk_id, text=content, distance=distance)
            for chunk_id, content, meta, distance in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0],
                results["distances"][0], strict=True,
            )
        ]
