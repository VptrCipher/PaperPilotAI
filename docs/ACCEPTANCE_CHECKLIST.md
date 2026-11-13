# Assignment 5 acceptance checklist

The build uses the seven criteria transcribed in the supplied brief. The original university PDF was unavailable in the attachment. This checklist records the project demonstration, with no claim about an official grade.

| # | Requirement | Source and function | Demonstration and test evidence | Status |
|---|---|---|---|---|
| 1 | Local LLM integration | `core/llm.py` · `installed_models`, `local_model`, `structured_call` | Qwen2.5 through Ollama generated a real summary against the FAIR PDF in Chrome. | PASS |
| 2 | Interactive GUI | `app.py` · upload flow, request form, `display_result` | Chrome uploaded the PDF, displayed 72 indexed chunks and a live summary with evidence, previewed and downloaded six slides, and verified clear/reset. | PASS |
| 3 | Prompt engineering | `prompts/templates.py` · `ROUTER`, `RETRIEVAL`, `AGENTS` | Inspect the routing examples, zero-shot task instructions, role messages, and structured JSON in the teaching panel. Live model generated distinct summary, concepts and viva payloads. | PASS |
| 4 | LangChain and LCEL | `core/llm.py` · `structured_call` | The live summary used the same LCEL prompt → ChatOllama → parser sequence for intent, retrieval decision, and generation. Pydantic validated the JSON. | PASS |
| 5 | Agentic RAG | `core/workflow.py` · `run_request`, `bounded_evidence` | The live revision reused five excerpts and shortened the answer without another search. A missing grant amount triggered one targeted retry and an insufficient-evidence response. An unqualified comparison produced a clarifying question without search. | PASS |
| 6 | Intent detection and routing | `core/workflow.py` · `run_request`, `generate` | Four natural-language requests selected the Summarizer, Concept-Extractor, Slide-Generator and Viva agents in the live workflow. | PASS |
| 7 | Vector database | `core/vector_store.py` · `PaperIndex.index`, `PaperIndex.search` | Live MiniLM embeddings and Chroma retrieved FAIR excerpts with PDF pages from 72 chunks indexed over 10 pages. Controlled-vector tests verified isolation and re-indexing. | PASS |

## Reproduce

```bash
python -m pytest -m "not live" -q
python -m pytest -m live -s
python -m streamlit run app.py
```

The final Windows run passed 22 tests, including 20 deterministic tests and two live integrations using Ollama 0.40.16, Qwen2.5 3B, and pinned MiniLM weights. The deterministic suite also passed 20 tests on Ubuntu 24.04 under WSL. Full live Ollama acceptance was exercised on Windows. Chrome downloaded a six-slide file, and a separate real six-slide export opened and rendered in Microsoft PowerPoint. The suite emitted five PyMuPDF SWIG deprecation warnings. See [Demo Guide](DEMO_GUIDE.md) for the browser sequence.
