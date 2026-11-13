"""Viva practice: type your own answer and get advisory feedback grounded in the paper.

The same local model, LCEL prompt and Pydantic validation as the other agents. The scores are advisory model
judgments, not a measurement of ability, and every cited page must be one of the retrieved excerpts.
"""
from dataclasses import dataclass
from typing import Callable

from core.llm import structured_call
from core.schemas import Evaluation
from core.workflow import bounded_evidence, evidence_text
from prompts.templates import EVALUATOR

MAX_ANSWER_CHARS = 2000


@dataclass
class Attempt:
    question: str
    answer: str
    evaluation: Evaluation
    evidence: list[dict]
    document_id: str


def validate_evaluation(result: Evaluation, pages: set[int]):
    if not set(result.source_pages) <= pages:
        raise ValueError(f"Use only the supplied PDF pages: {sorted(pages)}.")


def evaluate_answer(
    llm, index, question: str, answer: str, suggested: str, log: Callable[[str], None]
) -> Attempt:
    question, answer = question.strip(), answer.strip()
    if not answer or len(answer) > MAX_ANSWER_CHARS:
        raise ValueError(f"Write an answer of 1–{MAX_ANSWER_CHARS} characters.")
    if index is None or index.paper is None:
        raise ValueError("Index a research PDF before practising.")
    hits = index.search(f"{question}\n{answer[:300]}", 4) + index.search(question, 3)
    evidence = bounded_evidence(hits)
    if not evidence:
        raise ValueError("No paper excerpts were found for that question.")
    log(f"Viva practice · retrieved {len(evidence)} excerpts for the answer")
    pages = {chunk["page"] for chunk in evidence}
    result = structured_call(
        EVALUATOR, llm, Evaluation,
        {
            "question": question, "student_answer": answer, "reference_answer": suggested,
            "source_pages": sorted(pages), "document_context": evidence_text(evidence),
        },
        lambda value: validate_evaluation(value, pages),
    )
    log("Viva answer evaluated · scores are advisory model judgments")
    return Attempt(question, answer, result, evidence, index.paper.document_id)
