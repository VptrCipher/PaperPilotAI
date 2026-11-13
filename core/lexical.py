"""Offline lexical embeddings: hashed bag-of-words vectors.

No model, no download and no network. It plugs into ``PaperIndex`` through the same ``encode`` interface as
the MiniLM sentence-transformer, so the vector database and the agents are unchanged. It matches shared
vocabulary (keyword-style search), which makes it less capable than the semantic index on paraphrases.
"""
import math
import re
import zlib

import numpy as np

DIMENSIONS = 768
TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an and are as at be been by for from had has have in into is it its of on or that the their this "
    "these those to was were which while with".split()
)


def tokens(text: str) -> list[str]:
    """Lowercase words, without stop words, with a light fold of simple plurals."""
    out = []
    for word in TOKEN.findall(text.lower()):
        if len(word) < 2 or word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        out.append(word)
    return out


class LexicalEmbedder:
    """Same ``encode`` signature as SentenceTransformer, so ``PaperIndex`` can use either."""

    label = "Offline lexical"

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False, **_):
        vectors = np.zeros((len(texts), DIMENSIONS), dtype=np.float32)
        for row, text in enumerate(texts):
            counts: dict[str, int] = {}
            for word in tokens(text):
                counts[word] = counts.get(word, 0) + 1
            for word, count in counts.items():
                # crc32 is stable across runs and machines, unlike Python's salted hash().
                vectors[row, zlib.crc32(word.encode("utf-8")) % DIMENSIONS] += 1.0 + math.log(count)
            if not counts:
                # A query with no usable words matches everything equally instead of producing NaN.
                vectors[row, :] = 1.0
        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / np.where(norms == 0, 1.0, norms)
        return vectors
