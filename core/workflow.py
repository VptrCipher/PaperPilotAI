from dataclasses import dataclass, field
import re
from typing import Callable

from config import CONTEXT_CHARS, MAX_REQUEST_CHARS
from core.llm import structured_call
from core.schemas import Answer, Concepts, Decision, Route, Slides, Summary, Viva
from prompts.templates import AGENTS, RETRIEVAL, ROUTER

AGENT_NAMES = {
    "summary": "Summarizer Agent",
    "concepts": "Concept-Extractor Agent",
    "slides": "Slide-Generator Agent",
    "viva": "Viva Agent",
}
AGENT_DATA = {"summary": Summary, "concepts": Concepts, "slides": Slides, "viva": Viva}
PAPER_TOPICS = (
    "Abstract introduction research problem objectives and motivation",
    "Research approach methods methodology design data and techniques",
    "Key concepts findings results contributions discussion limitations and conclusion",
)
MISSING = "I couldn’t find enough evidence in the paper excerpts to answer that request."


@dataclass
class Turn:
    request: str
    intent: str
    document_id: str = ""
    action: str = ""
    message: str = ""
    answer: Answer | None = None
    evidence: list[dict] = field(default_factory=list)
    route: Route | None = None
    decision: Decision | None = None


def evidence_text(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[PDF page {chunk['page']}, chunk {chunk['id']}]\n{chunk['text']}"
        for chunk in chunks
    )


def bounded_evidence(chunks: list[dict]) -> list[dict]:
    chosen = []
    seen = set()
    size = 0
    for chunk in chunks:
        entry_size = len(chunk["text"]) + 60
        if chunk["id"] not in seen and size + entry_size <= CONTEXT_CHARS:
            chosen.append(chunk)
            seen.add(chunk["id"])
            size += entry_size
    return chosen


def difficulty_list(route: Route) -> list[str]:
    if route.difficulty != "mixed":
        return [route.difficulty] * route.question_count
    easy = (route.question_count * 4 + 5) // 10
    intermediate = (route.question_count * 4) // 10
    advanced = route.question_count - easy - intermediate
    return ["easy"] * easy + ["intermediate"] * intermediate + ["advanced"] * advanced


def validate_answer(answer: Answer, route: Route, pages: set[int]):
    if answer.status == "insufficient":
        if answer.data is not None:
            raise ValueError("Use data null for insufficient evidence.")
        return
    if answer.data is None:
        raise ValueError("Supply the requested data when status is ok.")
    if route.intent == "summary":
        items = [getattr(answer.data, name) for name in Summary.model_fields]
        if not any(item.source_pages for item in items):
            raise ValueError("Cite supported sections, or return insufficient.")
        for item in items:
            if not item.source_pages:
                item.text = "This information was not found in the retrieved excerpts."
    elif route.intent == "concepts":
        items = answer.data.concepts
        for item in items:
            # A cited concept is a paper concept; an uncited one is background. Repair rather than fail.
            item.kind = "paper" if item.source_pages else "background"
        if not any(item.source_pages for item in items):
            raise ValueError("Cite at least one paper concept, or return insufficient.")
    elif route.intent == "slides":
        items = answer.data.slides
        if len(items) != route.slide_count or any(not item.source_pages for item in items):
            raise ValueError(f"Generate {route.slide_count} slides with supporting pages on each.")
    else:
        items = answer.data.questions
        if [item.difficulty for item in items] != difficulty_list(route):
            raise ValueError(f"Use this ordered difficulty list: {difficulty_list(route)}.")
        if any(not item.source_pages for item in items):
            raise ValueError("Include supporting pages for every viva answer.")
    if any(not set(item.source_pages) <= pages for item in items):
        raise ValueError(f"Use only the supplied PDF pages: {sorted(pages)}.")


def generate(llm, route: Route, request: str, evidence: list[dict], previous: str, prior=None):
    pages = {chunk["page"] for chunk in evidence}
    settings = {
        "summary": "Use all eight summary fields and adapt depth to the user.",
        "concepts": "Return up to four concepts with short explanations. For a shortening request, keep just the main points.",
        "slides": f"Exactly {route.slide_count} slides.",
        "viva": f"Exactly {route.question_count} questions. Ordered difficulties: {difficulty_list(route)}.",
    }
    shortening = (
        route.intent == "concepts" and route.revision and isinstance(prior, Concepts)
        and re.search(r"\b(shorter|shorten|briefer|more concise|condense)\b", request, re.IGNORECASE)
    )
    if shortening:
        prior_chars = sum(len(item.explanation) for item in prior.concepts)
        settings["concepts"] += (
            f" Return just one or two main concepts in at most "
            f"{max(35, prior_chars * 2 // 3)} total explanation characters."
        )
    answer = structured_call(
        AGENTS[route.intent], llm, Answer[AGENT_DATA[route.intent]],
        {
            "user_request": request, "settings": settings[route.intent],
            "document_context": evidence_text(evidence), "source_pages": sorted(pages),
            "previous_output": previous,
        },
        lambda result: validate_answer(result, route, pages),
    )
    if shortening and answer.status == "ok":
        items = answer.data.concepts
        while len(items) > 1 and sum(len(item.explanation) for item in items) >= prior_chars:
            items.pop()
    if route.intent == "concepts" and answer.status == "ok":
        explanations = " ".join(item.explanation for item in answer.data.concepts)
        missing_fact = re.search(
            r"\b(?:not (?:reported|provided|stated|specified|mentioned|found|available)|"
            r"(?:does|do) not (?:report|provide|state|specify|mention)|no (?:specific )?information)\b",
            explanations, re.IGNORECASE,
        )
        exact_amount = re.search(r"\bexact\b.*\b(?:amount|cost|price|total)\b", request, re.I)
        if exact_amount:
            evidence_amounts = set(re.findall(r"[$€£]\s*[\d,.]+|\b[\d,.]+\s+(?:dollars|USD|euros|pounds)\b", evidence_text(evidence), re.I))
            reported_amounts = set(re.findall(r"[$€£]\s*[\d,.]+|\b[\d,.]+\s+(?:dollars|USD|euros|pounds)\b", explanations, re.I))
            if missing_fact or not (reported_amounts & evidence_amounts):
                return Answer[Concepts](status="insufficient", data=None, note="")
    if route.intent == "slides" and answer.status == "ok":
        # Some small models put their takeaway in the middle of a complete deck.
        # Move that existing slide to the end, preserving its bullets and citations.
        slides = answer.data.slides
        closing = next((
            i for i in range(len(slides) - 1, 0, -1)
            if re.search(r"conclu|takeaway|impact|implication|summary", slides[i].title, re.I)
        ), None)
        if closing is not None:
            slides.append(slides.pop(closing))
        slides[-1].title = "Conclusion"
    return answer


def run_request(
    request: str, llm, index, history: list[Turn],
    log: Callable[[str], None], preset: dict | None = None,
) -> Turn:
    request = request.strip()
    if not request or len(request) > MAX_REQUEST_CHARS:
        raise ValueError(f"Enter a request of 1–{MAX_REQUEST_CHARS} characters.")
    document_id = index.paper.document_id if index is not None and index.paper else ""
    current = [turn for turn in history if turn.document_id == document_id]
    last = next((turn for turn in reversed(current) if turn.answer), None)
    recent = "\n".join(
        f"{turn.intent}: {turn.request[:300]}\n{turn.message[:300]}"
        for turn in current[-2:]
    ) or "(no previous requests)"
    if last:
        recent = f"Last completed task: {last.intent}.\n" + recent
    if preset:
        route = Route.model_validate(preset)
        log(f"Intent selected with a quick action · {route.intent}")
    else:
        route = structured_call(
            ROUTER, llm, Route,
            {"user_request": request, "conversation_context": recent},
        )
        if not current and re.fullmatch(
            r"(?:explain|describe|summarize|clarify)\s+(?:the|that|this)\s+(?:comparison|difference)\s*[?.!]?",
            request, re.IGNORECASE,
        ):
            route.intent = "clarification"
            route.reason = "Comparison has no named referent"
            route.clarification = "Which methods, results, or concepts would you like me to compare?"
        if (
            last and not route.revision and route.intent in {"summary", "concepts"}
            and re.search(
                r"\b(?:make|keep|rewrite|shorten|simplify|condense)\b[^.?!]{0,40}\b(?:previous|last|above|earlier|that|it)\b"
                r"|\b(?:shorter|simpler|more concise)\b",
                request, re.IGNORECASE,
            )
        ):
            route.revision = True
            log("Follow-up phrasing recognised as a revision of the last result")
        if route.revision and last and route.intent in {"summary", "concepts"}:
            route.intent = last.intent
        if route.intent == "viva" and route.difficulty == "mixed":
            requested_level = re.search(
                r"\b(easy|beginner|intermediate|advanced)\s+(?:viva\s+)?(?:questions|answers)\b",
                request, re.IGNORECASE,
            )
            if requested_level:
                level = requested_level[1].lower()
                route.difficulty = "easy" if level == "beginner" else level
        log(f"Intent detected · {route.intent}")
    turn = Turn(request, route.intent, document_id, route=route)
    if route.intent == "general":
        turn.message = "Upload a text-based PDF to summarize it, explain concepts, build slides, or practice viva questions."
        return turn
    if route.intent == "clarification":
        turn.action = "clarify"
        turn.message = route.clarification.strip() or "Which part of the paper would you like help with?"
        log("Asked a clarifying question · no vector search")
        return turn
    if not document_id:
        turn.message = "Upload and index a research PDF before requesting paper-specific work."
        return turn

    log(f"Selected agent · {AGENT_NAMES[route.intent]}")
    previous = last.answer.model_dump_json()[:2500] if last else ""
    cached = last.evidence if last else []
    decision = structured_call(
        RETRIEVAL, llm, Decision,
        {
            "intent": route.intent, "user_request": request, "conversation_context": recent,
            "revision": route.revision,
            "previous_output": previous[:1200] if route.revision else "",
            "document_context": evidence_text(cached[:2])[:1400] if route.revision else "",
        },
    )
    turn.decision = decision
    turn.action = decision.action
    if turn.action == "clarify" and not decision.clarification.strip():
        turn.action = "retrieve"
        log("No specific clarification question supplied · searched the paper")
    if route.revision and cached and decision.action == "retrieve" and not decision.search_query.strip():
        turn.action = "reuse_context"
        log("Revision has current-paper excerpts and no new search topic · reused context")
    if turn.action == "reuse_context" and (not cached or not route.revision):
        turn.action = "retrieve"
        log("Reuse requires current-paper evidence and a revision request · retrieval required")
    log(f"Retrieval decision executed · {turn.action}")
    if turn.action == "clarify":
        turn.message = decision.clarification.strip() or "Which topic or comparison do you mean?"
        return turn

    query = decision.search_query.strip()[:MAX_REQUEST_CHARS] or request
    if turn.action == "reuse_context":
        evidence = cached
        log(f"Reused {len(cached)} chunks from the current paper · vector search skipped")
    else:
        broad = route.scope == "broad"
        queries = [query, *PAPER_TOPICS] if broad else [query]
        hits = []
        for search_query in queries:
            hits.extend(index.search(search_query, 2 if broad else 5))
        evidence = bounded_evidence(hits)
        log(f"ChromaDB searches · {len(queries)} · selected {len(evidence)} distinct chunks")
        previous = ""

    for attempt in range(2):
        if evidence:
            answer = generate(
                llm, route, request, evidence, previous,
                last.answer.data if previous and last else None,
            )
            if answer.status == "ok":
                turn.answer = answer
                turn.evidence = evidence
                if route.intent == "slides":
                    detail = f"{len(answer.data.slides)} slides"
                elif route.intent == "viva":
                    detail = f"{len(answer.data.questions)} viva questions"
                elif route.intent == "concepts":
                    detail = f"{len(answer.data.concepts)} concept explanations"
                else:
                    detail = "structured summary"
                log(f"Generated {detail}")
                return turn
        if attempt == 0:
            retry_query = f"{query}\n{request}" if query != request else f"Specific details reported about: {request}"
            extra = index.search(retry_query, 5)
            combined = bounded_evidence(extra + evidence)
            log(f"Evidence insufficient · ran one targeted ChromaDB retry ({len(extra)} matches)")
            if not ({chunk["id"] for chunk in combined} - {chunk["id"] for chunk in evidence}):
                break
            evidence = combined
            previous = ""

    turn.evidence = evidence
    turn.message = MISSING
    log("Returned an insufficient-evidence response")
    return turn
