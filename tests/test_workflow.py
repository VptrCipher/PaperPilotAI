import json
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

from core.workflow import MISSING, run_request


def route(intent, revision=False):
    return dict(
        intent=intent, revision=revision, scope="targeted", slide_count=6,
        question_count=10, difficulty="mixed", reason="task",
        clarification="Which methods should I compare?" if intent == "clarification" else "",
    )


def decision(action, clarification=""):
    return dict(action=action, search_query="research methodology", reason="test", clarification=clarification)


def answer(intent, page=1):
    section = dict(text="The team measured growth.", source_pages=[page])
    payloads = {
        "summary": {name: section for name in (
            "overview", "problem", "objective", "methodology",
            "findings", "contributions", "limitations", "conclusion",
        )},
        "concepts": {"concepts": [dict(name="Daily measurement", explanation="The team checked growth each day.", source_pages=[page], kind="paper")]},
        "slides": {"slides": [dict(title="Conclusion" if i == 5 else f"Heading {i}", bullets=["Researchers measured growth."], source_pages=[page]) for i in range(6)]},
        "viva": {"questions": [
            dict(question=f"Question {i}?", answer="The team measured growth.", difficulty=level, source_pages=[page])
            for i, level in enumerate(["easy"] * 4 + ["intermediate"] * 4 + ["advanced"] * 2)
        ]},
    }
    return dict(status="ok", note="", data=payloads[intent])


def model(*responses):
    pending = iter(responses)
    return RunnableLambda(lambda prompt, **kwargs: json.dumps(next(pending)))


class TestIndex:
    __test__ = False

    def __init__(self, digest="first", new_matches=False):
        self.paper = SimpleNamespace(document_id=digest)
        self.calls = []
        self.new_matches = new_matches

    def search(self, query, limit):
        self.calls.append(query)
        number = len(self.calls) if self.new_matches else 1
        return [dict(page=1, id=str(number), text="The researchers measured growth daily.")]


@pytest.mark.parametrize(("request_text", "intent"), [
    ("What is the gist of the paper?", "summary"),
    ("Walk me through their approach.", "concepts"),
    ("Build a six-page talk deck.", "slides"),
    ("What would an examiner ask me?", "viva"),
])
def test_dispatches_validated_model_route(request_text, intent):
    index = TestIndex()
    result = run_request(request_text, model(route(intent), decision("retrieve"), answer(intent)), index, [], print)
    assert result.intent == intent and result.answer.data
    assert len(index.calls) == 1


def test_revision_reuses_same_paper_and_new_fact_retrieves():
    index = TestIndex()
    prior = run_request("Explain methodology.", model(route("concepts"), decision("retrieve"), answer("concepts")), index, [], print)
    result = run_request("Make that shorter.", model(route("concepts", True), decision("reuse_context"), answer("concepts")), index, [prior], print)
    assert result.action == "reuse_context" and len(index.calls) == 1
    result = run_request("What software did they use?", model(route("concepts"), decision("reuse_context"), answer("concepts")), index, [prior], print)
    assert result.action == "retrieve" and len(index.calls) == 2


def test_replacement_does_not_reuse_old_evidence():
    index = TestIndex()
    prior = run_request("Explain methodology.", model(route("concepts"), decision("retrieve"), answer("concepts")), index, [], print)
    other = TestIndex("second")
    result = run_request("Shorten that.", model(route("concepts", True), decision("reuse_context"), answer("concepts")), other, [prior], print)
    assert result.document_id == "second" and result.action == "retrieve"
    assert len(other.calls) == 1


@pytest.mark.parametrize("model_route", ["clarification", "concepts"])
def test_clarification_avoids_search(model_route):
    index = TestIndex()
    result = run_request("Explain the comparison.", model(route(model_route), decision("clarify", "Which comparison?")), index, [], print)
    assert result.action == "clarify" and not index.calls and "?" in result.message


def test_missing_information_retries_once():
    index = TestIndex(new_matches=True)
    missing = dict(status="insufficient", note="", data=None)
    result = run_request("What was their funding amount?", model(route("concepts"), decision("retrieve"), missing, missing), index, [], print)
    assert not result.answer and result.message == MISSING and len(index.calls) == 2


def test_invalid_router_output_is_rejected_after_retry():
    with pytest.raises(ValueError, match="valid output"):
        run_request("Explain methodology.", model({"intent": "typo"}, {"intent": "typo"}), TestIndex(), [], print)


def test_bad_page_is_retried_then_rejected():
    with pytest.raises(ValueError, match="valid output"):
        run_request("Explain methodology.", model(
            route("concepts"), decision("retrieve"), answer("concepts", 99), answer("concepts", 99)
        ), TestIndex(), [], print)
