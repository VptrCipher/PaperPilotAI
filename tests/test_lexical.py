import numpy as np

from conftest import make_pdf
from core.lexical import DIMENSIONS, LexicalEmbedder, tokens
from core.pdf_processor import extract_paper
from core.vector_store import PaperIndex


def test_tokens_drop_stop_words_and_fold_simple_plurals():
    assert tokens("The telescopes were observing stars and glass") == ["telescope", "observing", "star", "glass"]


def test_vectors_are_deterministic_and_unit_length():
    embedder = LexicalEmbedder()
    first = embedder.encode(["optical telescope observations", "seedlings grew in the greenhouse"])
    again = LexicalEmbedder().encode(["optical telescope observations", "seedlings grew in the greenhouse"])
    assert first.shape == (2, DIMENSIONS)
    assert np.array_equal(first, again)
    assert np.allclose(np.linalg.norm(first, axis=1), 1.0)


def test_text_without_usable_words_still_gives_a_finite_vector():
    vector = LexicalEmbedder().encode(["the of and"])
    assert np.isfinite(vector).all()
    assert np.isclose(np.linalg.norm(vector), 1.0)


def test_lexical_index_retrieves_the_matching_page_with_real_chroma():
    astronomy = "We recorded distant galaxies with an optical telescope over many clear nights. "
    botany = "Seedlings grew faster under red light in the greenhouse trial across three weeks. "
    paper = extract_paper(make_pdf("Introduction\n" + astronomy * 6, "Results\n" + botany * 6), "mixed.pdf")
    index = PaperIndex(LexicalEmbedder(), "lexical")
    assert index.index(paper) is True
    assert index.mode == "lexical"
    assert index.search("optical telescope observations", 1)[0]["page"] == 1
    assert index.search("seedling growth in the greenhouse", 1)[0]["page"] == 2
    index.clear()
