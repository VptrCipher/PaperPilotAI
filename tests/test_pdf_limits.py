import pytest

from conftest import make_pdf
from config import MAX_PAGES, MAX_TEXT_CHARS
from core.pdf_processor import extract_paper

SENTENCE = "The observations were collected over many weeks using an optical telescope. "


def test_documented_limits():
    assert (MAX_PAGES, MAX_TEXT_CHARS) == (150, 1_000_000)


def test_a_paper_over_the_page_limit_is_refused(monkeypatch):
    monkeypatch.setattr("core.pdf_processor.MAX_PAGES", 3)
    with pytest.raises(ValueError, match="3 pages or fewer"):
        extract_paper(make_pdf(*[SENTENCE * 3] * 4), "long.pdf")


def test_a_paper_with_too_much_text_is_refused(monkeypatch):
    monkeypatch.setattr("core.pdf_processor.MAX_TEXT_CHARS", 200)
    with pytest.raises(ValueError, match="too much text"):
        extract_paper(make_pdf(*[SENTENCE * 2] * 3), "dense.pdf")


def test_a_normal_paper_is_within_the_limits():
    paper = extract_paper(make_pdf(*[SENTENCE * 8] * 3), "ok.pdf")
    assert paper.page_count == 3 and paper.chunks
