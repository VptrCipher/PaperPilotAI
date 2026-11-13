import os
from threading import Lock
from uuid import uuid4

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import chromadb
import numpy as np
from chromadb.config import Settings

from config import EMBEDDING_DIR
from core.lexical import LexicalEmbedder
from core.pdf_processor import Paper

ENCODE_LOCK = Lock()
RRF_K = 60  # reciprocal-rank-fusion constant


def embedding_weights_present() -> bool:
    """True when the pinned MiniLM weights were set up (python -m sample_data.setup_embeddings)."""
    return (EMBEDDING_DIR / "model.safetensors").is_file()


def load_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        str(EMBEDDING_DIR), device="cpu", local_files_only=True
    )


class PaperIndex:
    """One active collection per UI session, held in Chroma's in-memory client."""

    def __init__(self, embedder, mode="semantic"):
        self.embedder = embedder
        self.mode = mode  # "semantic" (MiniLM) or "lexical" (offline, no download)
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
        # Hybrid retrieval: exact-word vectors held beside the semantic ones, used to rescue passages whose
        # meaning match is weak but whose wording matches the question.
        self._words = LexicalEmbedder() if self.mode == "semantic" else None
        self._word_vectors = self._words.encode([c["text"] for c in paper.chunks]) if self._words else None
        return True

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if self.collection is None:
            raise ValueError("Index a PDF before searching.")
        pool = min(max(limit * 3, limit), self.collection.count())
        results = self.collection.query(
            query_embeddings=self._vectors([query]),
            n_results=pool,
            include=["documents", "metadatas", "distances"],
        )
        hits = [
            dict(meta, id=chunk_id, text=content, distance=distance)
            for chunk_id, content, meta, distance in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0],
                results["distances"][0], strict=True,
            )
        ]
        if self._words is None:
            return hits[:limit]
        # Reciprocal rank fusion of the semantic ranking and the exact-word ranking.
        scores = self._word_vectors @ self._words.encode([query])[0]
        chunks = self.paper.chunks
        word_rank = [chunks[i] for i in np.argsort(-scores)[:pool] if scores[i] > 0]
        fused: dict[str, float] = {}
        for ranking in (hits, word_rank):
            for position, hit in enumerate(ranking):
                fused[hit["id"]] = fused.get(hit["id"], 0.0) + 1.0 / (RRF_K + position + 1)
        by_id = {hit["id"]: hit for hit in hits}
        ordered = sorted(fused, key=fused.get, reverse=True)[:limit]
        out = []
        for chunk_id in ordered:
            hit = by_id.get(chunk_id)
            if hit is None:  # found by wording only
                chunk = next(c for c in chunks if c["id"] == chunk_id)
                hit = dict(chunk, distance=1.0)
            out.append(hit)
        return out
