from datetime import datetime

from core.practice import Attempt
from core.schemas import Answer, Concepts, Evaluation, Slides, Summary, Viva
from core.workflow import Turn
from utils.report import build_report

WHEN = datetime(2026, 11, 13, 12, 0)


def section(text="The team measured growth."):
    return dict(text=text, source_pages=[2])


def turn(intent, schema, data):
    answer = Answer[schema].model_validate(dict(status="ok", note="", data=data))
    return Turn(
        f"Request for {intent}", intent, "doc", action="retrieve", answer=answer,
        evidence=[dict(page=2, id="2-1", text="Excerpt")],
    )


def history():
    summary = {name: section() for name in Summary.model_fields}
    return [
        turn("summary", Summary, summary),
        turn("concepts", Concepts, {"concepts": [
            dict(name="Daily measurement", explanation="Growth was checked each day.", source_pages=[2], kind="paper"),
            dict(name="Control group", explanation="A group with no treatment.", source_pages=[], kind="background"),
        ]}),
        turn("slides", Slides, {"slides": [dict(title=f"Slide {i}", bullets=["A point."], source_pages=[2]) for i in range(5)]}),
        turn("viva", Viva, {"questions": [dict(question="What was measured?", answer="Growth.", difficulty="easy", source_pages=[2])]}),
        Turn("hello", "general", "doc", message="Upload a text-based PDF to begin."),
    ]


def attempts():
    value = Evaluation(correctness=4, depth=3, clarity=5, feedback="Good start.", next_step="Cite the page.", source_pages=[2])
    return [Attempt("What was measured?", "Growth over time.", value, [], "doc")]


def report(**overrides):
    values = dict(
        filename="paper.pdf", page_count=10, chunk_count=72, index_label="semantic MiniLM", model="qwen2.5:3b",
        history=history(), attempts=attempts(), activity=["PDF processed · 10 pages"], generated=WHEN,
    )
    return build_report(**{**values, **overrides})


def test_report_covers_every_result_type_with_pages():
    text = report()
    for expected in (
        "# PaperPilot AI session report", "Paper: paper.pdf", "10 pages, 72 indexed chunks (semantic MiniLM)",
        "Local model: qwen2.5:3b", "Generated: 2026-11-13 12:00",
        "**Paper overview.** The team measured growth. _(PDF pages 2)_",
        "**Daily measurement**", "**Control group** (general background)",
        "1. **Slide 0** _(PDF pages 2)_", "1. **What was measured?** _(easy)_", "Suggested answer: Growth.",
        "Handled by: Summarizer", "Retrieval: retrieve", "Upload a text-based PDF to begin.",
    ):
        assert expected in text, expected


def test_practice_scores_are_labelled_advisory_and_activity_is_real():
    text = report()
    assert "Correctness 4/5, depth 3/5, clarity 5/5 (advisory model judgment, not a grade)" in text
    assert "Your answer: Growth over time." in text
    assert "- PDF processed · 10 pages" in text


def test_an_empty_session_says_so_instead_of_inventing_content():
    text = report(history=[], attempts=[], activity=[], filename="", model="")
    assert "No requests were made." in text
    assert "No answers were practised." in text
    assert "No activity was recorded." in text
    assert "Paper: none" in text and "Local model: none selected" in text


def test_report_is_deterministic_for_a_fixed_time():
    assert report() == report()
