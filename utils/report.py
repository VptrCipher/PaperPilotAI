"""Session report: the conversation, the results, the viva attempts and the real activity trace, as Markdown."""
from datetime import datetime

SUMMARY_LABELS = {
    "overview": "Paper overview", "problem": "Research problem", "objective": "Objective",
    "methodology": "Methodology", "findings": "Key findings", "contributions": "Main contributions",
    "limitations": "Limitations", "conclusion": "Conclusion",
}
AGENTS = {"summary": "Summarizer", "concepts": "Concept-Extractor", "slides": "Slide-Generator", "viva": "Viva"}


def pages(values) -> str:
    return ("PDF pages " + ", ".join(map(str, sorted(set(values))))) if values else "No page cited"


def render_answer(turn) -> list[str]:
    data, lines = turn.answer.data, []
    if turn.intent == "summary":
        for key, label in SUMMARY_LABELS.items():
            section = getattr(data, key)
            lines += [f"**{label}.** {section.text} _({pages(section.source_pages)})_", ""]
    elif turn.intent == "concepts":
        for item in data.concepts:
            tag = " (general background)" if item.kind == "background" else ""
            lines += [f"- **{item.name}**{tag}: {item.explanation} _({pages(item.source_pages)})_"]
        lines.append("")
    elif turn.intent == "slides":
        for number, slide in enumerate(data.slides, start=1):
            lines += [f"{number}. **{slide.title}** _({pages(slide.source_pages)})_"]
            lines += [f"   - {bullet}" for bullet in slide.bullets]
        lines.append("")
    elif turn.intent == "viva":
        for number, item in enumerate(data.questions, start=1):
            lines += [
                f"{number}. **{item.question}** _({item.difficulty})_",
                f"   - Suggested answer: {item.answer} _({pages(item.source_pages)})_",
            ]
        lines.append("")
    return lines


def build_report(
    *, filename: str, page_count: int, chunk_count: int, index_label: str, model: str,
    history: list, attempts: list, activity: list[str], generated: datetime | None = None,
) -> str:
    stamp = (generated or datetime.now()).strftime("%Y-%m-%d %H:%M")
    out = [
        "# PaperPilot AI session report", "",
        f"- Paper: {filename or 'none'}",
        f"- Size: {page_count} pages, {chunk_count} indexed chunks ({index_label})",
        f"- Local model: {model or 'none selected'}",
        f"- Generated: {stamp}", "",
        "This report lists what happened in this session. Everything below came from the paper and the local "
        "model. Generated text can be wrong: check each statement against the cited PDF pages.", "",
        "## Requests and results", "",
    ]
    if not history:
        out += ["No requests were made.", ""]
    for number, turn in enumerate(history, start=1):
        agent = AGENTS.get(turn.intent, turn.intent.title())
        out += [f"### {number}. {turn.request}", "", f"- Handled by: {agent}"]
        if turn.action:
            out.append(f"- Retrieval: {turn.action.replace('_', ' ')}")
        if turn.evidence:
            out.append(f"- Evidence: {len(turn.evidence)} excerpts from {pages(c['page'] for c in turn.evidence)}")
        out.append("")
        if turn.answer:
            out += render_answer(turn)
        elif turn.message:
            out += [turn.message, ""]
    out += ["## Viva practice", ""]
    if not attempts:
        out += ["No answers were practised.", ""]
    for number, attempt in enumerate(attempts, start=1):
        ev = attempt.evaluation
        out += [
            f"### {number}. {attempt.question}", "",
            f"Your answer: {attempt.answer}", "",
            f"- Correctness {ev.correctness}/5, depth {ev.depth}/5, clarity {ev.clarity}/5 (advisory model judgment, not a grade)",
            f"- Feedback: {ev.feedback}", f"- Next step: {ev.next_step}", f"- {pages(ev.source_pages)}", "",
        ]
    out += ["## Agent activity", ""]
    out += [f"- {event}" for event in activity] or ["No activity was recorded."]
    return "\n".join(out) + "\n"
