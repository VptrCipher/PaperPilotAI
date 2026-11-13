from pathlib import Path

import streamlit as st

from config import DEFAULT_MODEL, MAX_REQUEST_CHARS, MAX_UPLOAD_MB, ROOT
from core.llm import installed_models, local_model
from core.pdf_processor import document_id, extract_paper
from core.vector_store import PaperIndex, load_embedder
from core.workflow import AGENT_NAMES, run_request
from prompts.templates import AGENTS, RETRIEVAL, ROUTER
from utils.pptx_export import build_pptx

st.set_page_config(page_title="PaperPilot AI", page_icon="📄", layout="wide")

ACTIONS = {
    "summary": ("Summarize Paper", "Summarize this paper in simple language."),
    "concepts": ("Extract Concepts", "Explain the methodology and important concepts."),
    "slides": ("Generate Slides", "Create a presentation based on this paper."),
    "viva": ("Prepare for Viva", "Generate practice questions and suggested answers."),
}


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
        st.caption("Few-shot routing and retrieval · zero-shot task prompts · JSON schema and Pydantic validation")
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
    "run_error": "",
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
                            index = PaperIndex(cached_embedder())
                        except Exception as exc:
                            raise ValueError(
                                "The embedding model could not be loaded. Run "
                                "python -m sample_data.setup_embeddings and retry."
                            ) from exc
                        st.session_state.index = index
                    try:
                        index.index(paper)
                    except Exception as exc:
                        raise ValueError("ChromaDB indexing failed. Retry this paper or use a smaller PDF.") from exc
                    note(f"PDF processed · {paper.page_count} pages")
                    note(f"Indexed {len(paper.chunks)} chunks in ChromaDB")
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
        st.caption(f"{paper.page_count} pages · {len(paper.chunks)} chunks")
    st.button("Clear conversation", on_click=clear_conversation, disabled=not st.session_state.history, width="stretch")
    st.button("Reset document", on_click=reset_upload, disabled=raw is None, width="stretch")

st.title("Research workspace", anchor=False)
st.caption("Turn a research paper into a summary, concept explanations, slides, and viva practice.")
if not paper:
    st.info("Upload a text-based research PDF from the sidebar, or use the included FAIR sample paper.")
else:
    with st.container(border=True):
        st.subheader(filename, anchor=False)
        st.caption(f"{paper.page_count} PDF pages · {len(paper.chunks)} indexed chunks")

with st.expander("Slide and viva settings"):
    left, middle, right = st.columns(3)
    slide_count = left.number_input("Slides", 5, 10, 6)
    question_count = middle.number_input("Viva questions", 1, 15, 10)
    difficulty = right.selectbox("Viva difficulty", ["mixed", "easy", "intermediate", "advanced"])
    st.caption("Settings apply to quick actions. Include preferred counts or difficulty in custom requests.")

request = ""
preset = None
for column, (intent, (label, prompt)) in zip(st.columns(4), ACTIONS.items(), strict=True):
    if column.button(label, disabled=not paper or not model, width="stretch"):
        request = prompt
        preset = {
            "intent": intent, "scope": "broad", "revision": False, "slide_count": slide_count,
            "question_count": question_count, "difficulty": difficulty,
            "reason": "Selected quick action", "clarification": "",
        }

with st.form("ask", clear_on_submit=True):
    user_input = st.text_input(
        "Ask anything about your research paper", max_chars=MAX_REQUEST_CHARS,
        placeholder="What is the paper’s main contribution?",
    )
    submitted = st.form_submit_button("Send request", disabled=not model, type="primary")
if submitted:
    request = user_input

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

tabs = st.tabs(["Summary", "Concepts", "Slides", "Viva"])
for tab, intent in zip(tabs, ACTIONS, strict=True):
    with tab:
        matching = [(pos, turn) for pos, turn in enumerate(history) if turn.intent == intent and turn.answer]
        if matching:
            position, turn = matching[-1]
            display_result(turn, position, filename)
        else:
            st.caption(f"Use {ACTIONS[intent][0]} or submit a related request to populate this view.")

with st.expander("Agent Activity", expanded=bool(st.session_state.activity)):
    if not st.session_state.activity:
        st.caption("Index a paper or submit a request to see real processing events.")
    for event in st.session_state.activity[-20:]:
        text(event)

teaching_panel(latest)
