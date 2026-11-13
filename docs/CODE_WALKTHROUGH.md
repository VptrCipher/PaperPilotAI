# Code walkthrough

## Start here

- `app.py` builds the sidebar, request form, task tabs, activity log, and prompt panel. `clear_paper` removes the current index and resets conversation. `display_result` renders the validated task data. **Viva question:** Why can changing a UI setting leave the paper ready? The session retains the index and compares the SHA-256 digest.
- `config.py` keeps model, upload, and context settings in one place. `sample_data/setup_embeddings.py` fetches the pinned weights during setup. **Viva question:** Which operation needs internet? The initial package and weight downloads.
- `core/pdf_processor.py` takes PDF bytes and returns a `Paper` with page count and chunk metadata. `extract_paper` validates input and processes each physical page independently. **Viva question:** Why use one-based pages? Readers can check a citation in a standard PDF viewer.
- `core/vector_store.py` accepts a `Paper` and a local embedder. `index` builds a Chroma collection, and `search` returns evidence dictionaries with page metadata. **Viva question:** Why use the same encoder? It places the request and paper text into the same vector space.
- `core/llm.py` checks installed models and runs the model/prompt/parser chain. `structured_call` takes values and a schema, returning validated data. **Viva question:** What happens if JSON fails? The chain gets one correction attempt, after which the UI displays an error.
- `prompts/templates.py` holds the router, retrieval, and four task prompts. The router's example messages demonstrate intent, counts, and revision classification. **Viva question:** Why are excerpts in the user message? They are research data supplied to the role defined by the system message.
- `core/schemas.py` defines allowable intents, decisions, and task payloads. `core/workflow.py` combines them with the index and the model. Its `run_request` function returns one `Turn`. **Viva question:** Where is the retrieval decision executed? In the branch on `turn.action`.
- `utils/pptx_export.py` converts `Slides` to file bytes. `build_pptx` builds each editable slide with an academic layout and page footer. **Viva question:** How do you know it creates a real file? The test opens the returned bytes using python-pptx and reads the six slides.
- `tests/` holds PDF/Chroma, workflow, export, and live-model verification. **Viva question:** What does a mocked routing test prove? That the application validates and dispatches a route supplied by a model-shaped test double.

## Follow one upload through a viva answer

1. The sidebar reads the PDF bytes. `document_id(raw)` hashes those bytes. If the same digest is already active, the current index is used.
2. `extract_paper(raw, filename)` opens the PDF, extracts text, splits it, and adds the one-based PDF page to each chunk. It returns a `Paper`.
3. `cached_embedder()` loads MiniLM once per Streamlit process. `index.index(paper)` encodes batches and inserts text, vectors, and metadata in Chroma.
4. The student submits “Generate ten viva questions with easy answers.” The form calls `run_request` with the local model, current index, and current history.
5. `structured_call(ROUTER, ...)` produces a validated route. The expected intent is `viva` with count 10 and difficulty `easy`.
6. `structured_call(RETRIEVAL, ...)` chooses an action. A fresh whole-paper request searches Chroma and gathers excerpts from several paper topics.
7. `generate` builds a task input with the exact difficulty list, excerpt text, and allowed page numbers. It calls the Viva prompt through LCEL.
8. `validate_answer` checks the difficulty list and source pages. The app appends the result to history and shows question cards. **Reveal suggested answer** displays the answer and its page reference.

## Read the LCEL block

```python
model = llm.bind(format=schema.model_json_schema())
chain = prompt | model | StrOutputParser()
raw = chain.invoke({**values, "format_feedback": ""})
result = schema.model_validate_json(raw)
```

- The first line sends Ollama a JSON schema describing the shape it should emit.
- The second line connects message formatting, model generation, and extraction of the message text.
- The third line supplies values to the prompt and executes the chain.
- The fourth line converts JSON into the expected Python object. The workflow then checks page membership and exact counts.

## Read the routing branch

A `clarify` result returns a brief question. A valid revision can reuse the same paper's evidence. Otherwise the workflow searches Chroma. It saves the evidence with the result so a later revision can reuse it. If the generator reports insufficient evidence, the workflow can make one targeted search. A change of paper clears the UI history, and the workflow independently filters incoming turns by document ID.
