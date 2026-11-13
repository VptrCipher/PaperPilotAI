import json
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

from core.practice import MAX_ANSWER_CHARS, evaluate_answer


def evaluation(page=1, correctness=4):
    return dict(
        correctness=correctness, depth=3, clarity=4,
        feedback="You named the method and the main result. You did not mention the limitation.",
        next_step="Add the limitation the paper states on this page.", source_pages=[page],
    )


def model(*responses):
    pending = iter(responses)
    calls = []

    def respond(prompt, **kwargs):
        calls.append(prompt)
        return json.dumps(next(pending))

    llm = RunnableLambda(respond)
    llm.calls = calls
    return llm


class FakeIndex:
    def __init__(self, with_paper=True):
        self.paper = SimpleNamespace(document_id="doc") if with_paper else None
        self.queries = []

    def search(self, query, limit):
        self.queries.append(query)
        return [dict(page=1, id="1-1", text="The researchers measured growth daily and report one limitation.")]


def run(llm, answer="They measured growth daily.", index=None, log=None):
    return evaluate_answer(
        llm, index if index is not None else FakeIndex(), "What did the researchers measure?",
        answer, "They measured growth daily.", (log if log is not None else []).append,
    )


def test_feedback_is_validated_grounded_and_logged_as_advisory():
    events = []
    attempt = run(model(evaluation()), log=events)
    assert (attempt.evaluation.correctness, attempt.evaluation.depth, attempt.evaluation.clarity) == (4, 3, 4)
    assert attempt.evaluation.source_pages == [1]
    assert attempt.evidence and attempt.document_id == "doc"
    assert any("advisory" in event for event in events)


def test_the_answer_and_question_both_drive_retrieval():
    index = FakeIndex()
    run(model(evaluation()), index=index)
    assert any("They measured growth daily." in query for query in index.queries)
    assert any(query == "What did the researchers measure?" for query in index.queries)


@pytest.mark.parametrize("answer", ["", "   ", "x" * (MAX_ANSWER_CHARS + 1)])
def test_empty_or_oversized_answers_are_refused(answer):
    with pytest.raises(ValueError, match="1–2000 characters"):
        run(model(evaluation()), answer=answer)


def test_a_paper_must_be_indexed_first():
    with pytest.raises(ValueError, match="Index a research PDF"):
        run(model(evaluation()), index=FakeIndex(with_paper=False))
    with pytest.raises(ValueError, match="Index a research PDF"):
        evaluate_answer(model(evaluation()), None, "Q?", "A", "ref", lambda _: None)


def test_an_out_of_range_score_is_corrected_on_the_one_retry():
    llm = model(evaluation(correctness=9), evaluation(correctness=3))
    attempt = run(llm)
    assert attempt.evaluation.correctness == 3
    assert len(llm.calls) == 2


def test_citing_a_page_that_was_not_retrieved_is_rejected_after_the_retry():
    llm = model(evaluation(page=7), evaluation(page=7))
    with pytest.raises(ValueError, match="could not produce valid output"):
        run(llm)
    assert len(llm.calls) == 2
