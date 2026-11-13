"""Opt in with pytest -m live. Uses the real PDF, MiniLM, Chroma and Ollama."""
import os
from io import BytesIO
from pathlib import Path

import pytest
from pptx import Presentation

from config import DEFAULT_MODEL
from core.llm import installed_models, local_model
from core.pdf_processor import extract_paper
from core.vector_store import PaperIndex, load_embedder
from core.workflow import MISSING, run_request
from utils.pptx_export import build_pptx

pytestmark = pytest.mark.live


@pytest.fixture
def live_index(demo_pdf):
    pdf = demo_pdf
    index = PaperIndex(load_embedder())
    index.index(extract_paper(pdf.read_bytes(), pdf.name))
    yield index
    index.clear()


def test_real_embeddings_and_chroma(live_index):
    hits = live_index.search("Findable Accessible Interoperable Reusable principles")
    assert hits and any("FAIR" in hit["text"] for hit in hits)
    assert all(1 <= hit["page"] <= live_index.paper.page_count for hit in hits)
    print(f"Indexed {len(live_index.paper.chunks)} chunks across {live_index.paper.page_count} pages.")


def test_live_assignment(live_index):
    name = os.getenv("PAPERPILOT_TEST_MODEL", DEFAULT_MODEL)
    assert name in installed_models(), f"Install {name} and start Ollama."
    llm = local_model(name)
    history = []

    def ask(request):
        turn = run_request(request, llm, live_index, history, print)
        history.append(turn)
        print(f"{turn.intent} / {turn.action} / pages {sorted({x['page'] for x in turn.evidence})}")
        return turn

    summary = ask("Summarize this paper in simple language.")
    assert summary.intent == "summary" and summary.action == "retrieve" and summary.answer
    concepts = ask("Explain the methodology and important concepts.")
    assert concepts.intent == "concepts" and concepts.answer
    followup = ask("Make your previous explanation shorter.")
    assert followup.intent == "concepts" and followup.action == "reuse_context" and followup.answer
    assert followup.evidence == concepts.evidence
    original_chars = sum(len(item.explanation) for item in concepts.answer.data.concepts)
    revised_chars = sum(len(item.explanation) for item in followup.answer.data.concepts)
    assert revised_chars < original_chars
    slides = ask("Create six presentation slides based on this paper.")
    assert slides.intent == "slides" and slides.answer
    deck = build_pptx(slides.answer.data)
    assert len(Presentation(BytesIO(deck)).slides) == 6
    if destination := os.getenv("PAPERPILOT_DEMO_PPTX"):
        Path(destination).write_bytes(deck)
    viva = ask("Generate ten viva questions with easy answers.")
    assert viva.intent == "viva" and viva.answer
    assert len(viva.answer.data.questions) == 10
    assert {item.difficulty for item in viva.answer.data.questions} == {"easy"}
    missing = ask("What was the exact dollar amount of the authors’ grant from the Martian Science Agency?")
    assert missing.message == MISSING
    history.clear()
    clarification = ask("Explain the comparison.")
    assert clarification.action == "clarify" and clarification.message.endswith("?")
