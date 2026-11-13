from pathlib import Path
from ui.workspace_view import hero, workspace_controls, workspace_results
import json

import streamlit as st

from config import DEFAULT_MODEL, MAX_REQUEST_CHARS, MAX_UPLOAD_MB, ROOT
from core.llm import installed_models, local_model
from core.lexical import LexicalEmbedder
from core.pdf_processor import document_id, extract_paper
from core.practice import MAX_ANSWER_CHARS, evaluate_answer
from core.vector_store import PaperIndex, embedding_weights_present, load_embedder
from core.workflow import AGENT_NAMES, run_request
from prompts.templates import AGENTS, RETRIEVAL, ROUTER
from utils.pptx_export import build_pptx
from utils.report import build_report

st.set_page_config(page_title="PaperPilot AI", page_icon="📄", layout="wide")

ACTIONS = {
    "summary": ("Summarize Paper", "Summarize this paper in simple language."),
    "concepts": ("Extract Concepts", "Explain the methodology and important concepts."),
    "slides": ("Generate Slides", "Create a presentation based on this paper."),
    "viva": ("Prepare for Viva", "Generate practice questions and suggested answers."),
}


INDEX_MODES = {
    "Semantic · MiniLM": "semantic",
    "Offline lexical · no download": "lexical",
}
INDEX_LABELS = {"semantic": "semantic MiniLM index", "lexical": "offline lexical index"}


@st.cache_resource(show_spinner=False)
def cached_embedder():
    return load_embedder()


@st.cache_data(ttl=8, show_spinner=False)
def model_status():
    try:
        return True, installed_models()
    except Exception:
        return False, []


def note(event):
    st.session_state.activity.append(event)
    del st.session_state.activity[:-80]


def clear_conversation():
    st.session_state.history = []
    st.session_state.exports = {}
    st.session_state.activity = []
    st.session_state.practice = {}
    st.session_state.run_error = ""
    if st.session_state.index is not None and st.session_state.index.paper:
        note(f"Paper ready · {len(st.session_state.index.paper.chunks)} indexed chunks")


def clear_paper():
    if st.session_state.index is not None:
        st.session_state.index.clear()
    clear_conversation()
    st.session_state.failed_digest = None
    st.session_state.upload_error = ""


def reset_upload():
    clear_paper()
    st.session_state.upload_key += 1


def choose_sample():
    reset_upload()
    st.session_state.sample_key = st.session_state.upload_key


def cite(pages):
    if pages:
        st.caption("PDF pages " + ", ".join(map(str, sorted(set(pages)))))


def text(value):
    # Plain text avoids rendering model-supplied links or remote images.
    st.text(value)


def practice_panel(position, number, item):
    """Type an answer to a viva question and get advisory feedback from the local model."""
    key = f"{position}:{number}"
    with st.expander("Practise your answer"):
        with st.form(f"practice_{position}_{number}", border=False):
            mine = st.text_area(
                "Your answer", key=f"mine_{key}", max_chars=MAX_ANSWER_CHARS, height=110,
                placeholder="Answer as you would in the viva, then ask for feedback.",
            )
            ask = st.form_submit_button("Get feedback", disabled=not model)
        if ask:
            try:
                with st.spinner(f"Checking your answer with {model}…"):
                    st.session_state.practice[key] = evaluate_answer(
                        local_model(model), st.session_state.index,
                        item.question, mine, item.answer, note,
                    )
            except ValueError as exc:
                st.warning(str(exc))
            except Exception:
                st.warning("The local request failed. Check Ollama and ChromaDB, then try again.")
        attempt = st.session_state.practice.get(key)
        if attempt:
            verdict = attempt.evaluation
            first, second, third = st.columns(3)
            first.metric("Correctness", f"{verdict.correctness}/5")
            second.metric("Depth", f"{verdict.depth}/5")
            third.metric("Clarity", f"{verdict.clarity}/5")
            text(verdict.feedback)
            text("Next step · " + verdict.next_step)
            cite(verdict.source_pages)
            st.caption("Advisory judgment from the local model, not a grade. Check the cited pages.")


def display_result(turn, position, filename):
    st.caption(f"Request · {turn.request}")
    if not turn.answer:
        st.info(turn.message)
        return
    answer = turn.answer
    if answer.note:
        text(answer.note)
    data = answer.data
    if turn.intent == "summary":
        labels = {
            "overview": "Paper overview", "problem": "Research problem",
            "objective": "Objective", "methodology": "Methodology",
            "findings": "Key findings", "contributions": "Main contributions",
            "limitations": "Limitations", "conclusion": "Conclusion",
        }
        for key, label in labels.items():
            section = getattr(data, key)
            st.markdown(f"#### {label}")
            text(section.text)
            cite(section.source_pages)
    elif turn.intent == "concepts":
        for item in data.concepts:
            with st.container(border=True):
                st.subheader(item.name, anchor=False)
                if item.kind == "background":
                    st.caption("General background")
                text(item.explanation)
                cite(item.source_pages)
    elif turn.intent == "slides":
        if position in st.session_state.exports:
            st.download_button(
                "Download PowerPoint", st.session_state.exports[position],
                file_name=f"{Path(filename).stem}-presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key=f"export_{position}",
                on_click="ignore",
            )
        for number, item in enumerate(data.slides, start=1):
            with st.container(border=True):
                st.caption(f"Slide {number} of {len(data.slides)}")
                st.subheader(item.title, anchor=False)
                for bullet in item.bullets:
                    text("• " + bullet)
                cite(item.source_pages)
    elif turn.intent == "viva":
        show = st.toggle("Show all suggested answers", key=f"answers_{position}")
        for number, item in enumerate(data.questions, start=1):
            with st.container(border=True):
                st.caption(f"Question {number} · {item.difficulty.title()}")
                text(item.question)
                if show:
                    text(item.answer)
                    cite(item.source_pages)
                else:
                    with st.expander("Reveal suggested answer"):
                        text(item.answer)
                        cite(item.source_pages)
                practice_panel(position, number, item)

    if turn.evidence:
        with st.expander("Paper evidence"):
            for chunk in turn.evidence:
                st.caption(f"PDF page {chunk['page']} · Chunk {chunk['id']}")
                text(chunk["text"])


def teaching_panel(turn):
    with st.expander("How this request was processed"):
        if turn is None:
            st.caption("Submit a request to see the routing, retrieval, and prompt templates.")
            return
        st.write(f"Intent · {turn.intent}")
        if turn.route:
            text(f"Routing label · {turn.route.reason}")
        if turn.intent in AGENT_NAMES:
            st.write(AGENT_NAMES[turn.intent])
        if turn.action:
            st.write(f"Executed action · {turn.action}")
        if turn.decision:
            text(f"Model retrieval choice · {turn.decision.action} · {turn.decision.reason}")
        cite([chunk["page"] for chunk in turn.evidence])
        st.caption(
            "Few-shot routing and retrieval · zero-shot task prompts · JSON schema and Pydantic validation · "
            "reflection: an invalid answer is returned to the model once with the validation errors as feedback"
        )
        st.code("model = llm.bind(format=schema_json, **options)\nchain = prompt | model | StrOutputParser()\nraw = chain.invoke(prompt_values)\nresult = schema.model_validate_json(raw)", language="python")
        for label, template in (
            ("Intent Router · few-shot", ROUTER),
            ("Retrieval Decision · few-shot", RETRIEVAL),
            ("Task agent · zero-shot", AGENTS.get(turn.intent)),
        ):
            if template is not None:
                st.markdown(f"**{label}**")
                st.code(template.pretty_repr(), language=None)
        if turn.answer:
            st.json(turn.answer.model_dump(), expanded=False)


for key, value in {
    "index": None, "history": [], "exports": {}, "activity": [],
    "failed_digest": None, "upload_error": "", "upload_key": 0,
    "run_error": "", "practice": {}, "index_mode": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.title("PaperPilot AI", anchor=False)
    st.caption("Research, presentation & viva assistant")
    online, models = model_status()
    if online and models:
        st.success("Ollama connected")
        model = st.selectbox("Local model", models, index=models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0)
        if DEFAULT_MODEL not in models:
            st.caption(f"Recommended model setup: ollama pull {DEFAULT_MODEL}")
    else:
        model = None
        if online:
            st.warning("Ollama is running. Install a local model to continue.")
        else:
            st.warning("Start the Ollama desktop app or run `ollama serve`.")
        st.code(f"ollama pull {DEFAULT_MODEL}", language="bash")
    if st.button("Refresh connection"):
        model_status.clear()
        st.rerun()

    semantic_ready = embedding_weights_present()
    index_choice = st.selectbox(
        "Search index", list(INDEX_MODES), index=0 if semantic_ready else 1,
        help="Semantic uses the MiniLM weights from setup. Offline lexical needs no download and matches shared words.",
    )
    index_mode = INDEX_MODES[index_choice]
    if index_mode == "semantic" and not semantic_ready:
        st.caption("MiniLM is not set up. Run python -m sample_data.setup_embeddings, or choose the offline index.")
    if st.session_state.index_mode not in (None, index_mode):
        clear_paper()
        st.session_state.index = None
    st.session_state.index_mode = index_mode

    st.divider()
    upload = st.file_uploader(
        f"Research paper · up to {MAX_UPLOAD_MB} MB", type="pdf",
        key=f"pdf_{st.session_state.upload_key}",
    )
    st.button("Use the FAIR sample paper", on_click=choose_sample, width="stretch")
    if upload is not None:
        st.session_state.pop("sample_key", None)
        filename, raw = upload.name, upload.getvalue()
    elif st.session_state.get("sample_key") == st.session_state.upload_key:
        sample = ROOT / "sample_data" / "fair-principles.pdf"
        filename, raw = sample.name, sample.read_bytes()
    else:
        filename, raw = "", None

    index = st.session_state.index
    current = index.paper if index is not None else None
    if raw is None and current:
        clear_paper()
    if raw is not None:
        digest = document_id(raw)
        if (current is None or digest != current.document_id) and digest != st.session_state.failed_digest:
            clear_paper()
            try:
                with st.spinner("Extracting text and indexing paper…"):
                    paper = extract_paper(raw, filename)
                    if index is None:
                        try:
                            embedder = cached_embedder() if index_mode == "semantic" else LexicalEmbedder()
                            index = PaperIndex(embedder, index_mode)
                        except Exception as exc:
                            raise ValueError(
                                "The embedding model could not be loaded. Run "
                                "python -m sample_data.setup_embeddings, or choose the offline lexical index, and retry."
                            ) from exc
                        st.session_state.index = index
                    try:
                        index.index(paper)
                    except Exception as exc:
                        raise ValueError("ChromaDB indexing failed. Retry this paper or use a smaller PDF.") from exc
                    note(f"PDF processed · {paper.page_count} pages")
                    note(f"Indexed {len(paper.chunks)} chunks in ChromaDB · {INDEX_LABELS[index.mode]}")
            except ValueError as exc:
                st.session_state.failed_digest = digest
                st.session_state.upload_error = str(exc)

    paper = index.paper if index is not None else None
    if st.session_state.upload_error:
        st.error(st.session_state.upload_error)
        if st.button("Retry processing"):
            st.session_state.failed_digest = None
            st.rerun()
    if paper:
        st.success("Paper indexed")
        text(filename)
        st.caption(f"{paper.page_count} pages · {len(paper.chunks)} chunks · {INDEX_LABELS[index.mode]}")
    st.button("Clear conversation", on_click=clear_conversation, disabled=not st.session_state.history, width="stretch")
    st.button("Reset document", on_click=reset_upload, disabled=raw is None, width="stretch")
    if st.session_state.history or st.session_state.practice:
        st.download_button(
            "Download session report",
            build_report(
                filename=filename, page_count=paper.page_count if paper else 0,
                chunk_count=len(paper.chunks) if paper else 0,
                index_label=INDEX_LABELS.get(index.mode, "") if index is not None else "",
                model=model or "", history=st.session_state.history,
                attempts=list(st.session_state.practice.values()), activity=st.session_state.activity,
            ),
            file_name=f"{Path(filename).stem or 'paperpilot'}-session-report.md",
            mime="text/markdown", width="stretch", on_click="ignore", key="session_report",
        )

ui_dir = ROOT / "ui"
workspace = json.loads((ui_dir / "workspace.json").read_text(encoding="utf-8"))
st.html(ui_dir / "workspace.css")
hero(workspace)
request, submitted, preset = workspace_controls(paper, model, filename, MAX_REQUEST_CHARS, ACTIONS)

if (request or submitted) and model:
    st.session_state.run_error = ""
    try:
        with st.spinner(f"Working with {model}…"):
            turn = run_request(
                request, local_model(model), index, st.session_state.history, note, preset
            )
            position = len(st.session_state.history)
            st.session_state.history.append(turn)
            if turn.answer and turn.intent == "slides":
                try:
                    st.session_state.exports[position] = build_pptx(turn.answer.data)
                    note("PowerPoint file created")
                except Exception:
                    st.session_state.run_error = "PowerPoint export failed. The slides are available in the preview."
    except ValueError as exc:
        st.session_state.run_error = str(exc)
    except Exception:
        st.session_state.run_error = (
            "The local request failed. Check Ollama and ChromaDB, refresh the connection, "
            "and try a shorter request or another installed model."
        )
    if st.session_state.run_error:
        note("Request needs attention · see the workspace message")

if st.session_state.run_error:
    st.warning(st.session_state.run_error)

history = st.session_state.history
latest = history[-1] if history else None
if latest and not latest.answer:
    st.info(latest.message)
    if latest.evidence:
        with st.expander("Excerpts checked"):
            for chunk in latest.evidence:
                cite([chunk["page"]])
                text(chunk["text"])

workspace_results(history, ACTIONS, display_result, filename)

with st.expander("Agent Activity", expanded=bool(st.session_state.activity)):
    if not st.session_state.activity:
        st.caption("Index a paper or submit a request to see real processing events.")
    for event in st.session_state.activity[-20:]:
        text(event)

teaching_panel(latest)
