import numpy as np

from core.pdf_processor import Paper
from core.vector_store import PaperIndex


class MisleadingEmbedder:
    """A semantic embedder that ranks the wrong passage first for the query below."""

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False, **_):
        out = []
        for text in texts:
            vector = np.zeros(4, dtype=np.float32)
            if text.startswith("What"):  # the query
                vector[0] = 1.0
            elif "decoy" in text:
                vector[0] = 0.99
                vector[1] = 0.14
            else:
                vector[2] = 1.0
            out.append(vector / np.linalg.norm(vector))
        return np.array(out)


def paper():
    chunks = [
        dict(id="1-1", page=1, text="A decoy passage about unrelated housekeeping and acknowledgements."),
        dict(id="2-1", page=2, text="The kelvinometer calibration drifted by two percent over the campaign."),
        dict(id="3-1", page=3, text="Another background passage about funding."),
    ]
    return Paper(document_id="doc", filename="p.pdf", page_count=3, chunks=chunks)


QUESTION = "What drift did the kelvinometer calibration show?"


def test_semantic_only_search_misses_the_passage_with_the_matching_wording():
    index = PaperIndex(MisleadingEmbedder(), mode="lexical")  # lexical mode: no word fusion
    index.index(paper())
    assert index.search(QUESTION, 1)[0]["id"] == "1-1"


def test_hybrid_search_rescues_it_through_exact_wording():
    index = PaperIndex(MisleadingEmbedder(), mode="semantic")
    index.index(paper())
    assert index.search(QUESTION, 1)[0]["id"] == "2-1"
    assert {hit["id"] for hit in index.search(QUESTION, 3)} == {"1-1", "2-1", "3-1"}
