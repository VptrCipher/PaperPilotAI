import numpy as np
import pytest

from core.pdf_processor import extract_paper
from core.vector_store import PaperIndex
from conftest import make_pdf


class ToyEmbedder:
    """Controlled vectors test Chroma mechanics independently of model weights."""

    def encode(self, texts, **kwargs):
        return np.array([
            [1.0, 0.0] if "telescope" in text.lower() else [0.0, 1.0] for text in texts
        ])


def test_extract_preserves_page_and_sections():
    content = "The observations were collected over many weeks using an optical telescope."
    paper = extract_paper(make_pdf("Introduction\n" + (content + " ") * 25, "Results\n" + content), "a.pdf")
    assert paper.page_count == 2
    assert {chunk["page"] for chunk in paper.chunks} == {1, 2}
    assert len(paper.chunks) > 2
    assert {chunk["section"] for chunk in paper.chunks} == {"Introduction", "Results"}
    assert all(len(chunk["text"]) <= 1000 for chunk in paper.chunks)


@pytest.mark.parametrize("data, message", [
    (b"", "empty"), (b"hello", "header"), (b"%PDF- broken", "could not be read"),
])
def test_invalid_pdf(data, message):
    with pytest.raises(ValueError, match=message):
        extract_paper(data, "invalid.pdf")


def test_scan_or_blank_page():
    with pytest.raises(ValueError, match="OCR"):
        extract_paper(make_pdf(""), "scan.pdf")


def test_password_protected():
    with pytest.raises(ValueError, match="password-protected"):
        extract_paper(make_pdf("Protected text.", password=True), "private.pdf")


def test_index_search_repeat_and_replace():
    first = extract_paper(make_pdf(
        "Seedlings were measured every day as part of the greenhouse study.",
        "The optical telescope recorded the apparent brightness of nearby stars.",
    ), "first.pdf")
    second = extract_paper(make_pdf(
        "The second study examined growth in greenhouse seedlings under red light."
    ), "second.pdf")
    index = PaperIndex(ToyEmbedder())
    try:
        assert index.index(first)
        assert not index.index(first)
        assert index.collection.count() == len(first.chunks)
        hit = index.search("telescope", 1)[0]
        assert hit["page"] == 2 and hit["document_id"] == first.document_id
        old_collection = index.collection.name
        assert index.index(second)
        assert old_collection not in [collection.name for collection in index.client.list_collections()]
        assert {hit["document_id"] for hit in index.search("telescope")} == {second.document_id}
    finally:
        index.clear()
