# PaperPilot AI

**Assignment 5 · Paper-to-Presentation & Viva Agent**

PaperPilot AI helps students turn one text-based research paper into a summary, concept explanations, a presentation, and viva practice. It shows the PDF excerpts used for each result and the routing and retrieval actions that led to it.

## Workspace preview

DesignForge generates the ember workspace from `ui-brief.json`. Streamlit loads the generated layout, theme, and styles from `ui/` while keeping the existing PDF, Ollama, retrieval, and export controls.

![Desktop workspace](ui/desktop.png)

[View the mobile workspace](ui/mobile.png).

## Quick start

Use Python 3.12 (the version used for Windows verification). Run these commands from the directory containing `app.py`.

### Windows · PowerShell

Install Ollama using the [official Windows installer](https://ollama.com/download/windows). Open Ollama, then use PowerShell.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
python -m pip install -r requirements.txt
python -m sample_data.setup_embeddings
ollama pull qwen2.5:3b
python -m streamlit run app.py
```

If activation is disabled in PowerShell, use `.\.venv\Scripts\python.exe` in place of `python`. If Ollama is installed as a standalone CLI, run `ollama serve` in a separate terminal before pulling the model.

### Linux · Bash

Install Python 3.12 with its venv module and [Ollama for Linux](https://docs.ollama.com/linux). If Ollama is installed without a service, leave `ollama serve` running in another terminal.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
python -m pip install -r requirements.txt
python -m sample_data.setup_embeddings
ollama pull qwen2.5:3b
python -m streamlit run app.py
```

The model pull downloads about 1.9 GB. Allow several GB of extra free disk space for packages, caches, and the Ollama runtime. You can select another installed local instruction model in the sidebar. The embedder uses the cache under `HF_HOME`, or `~/.cache/huggingface` if unset. Use the same setting at setup and launch. For Ollama on a different local port, set `PAPERPILOT_OLLAMA_PORT` before starting Streamlit.

Open [the local workspace](http://127.0.0.1:8501) and use the FAIR sample or upload your own PDF. Ollama and Streamlit listen on loopback. You can disable Ollama cloud features by setting `OLLAMA_NO_CLOUD=1` before starting the Ollama server. PaperPilot uses a local Ollama endpoint and omits cloud model tags from the selector. Dependencies and model weights need network access during setup. PDF processing, embedding, search, generation, and export run locally afterward.

## Try these requests

1. “Summarize this paper in simple language.”
2. “Explain the methodology and important concepts.”
3. “Make your previous explanation shorter.”
4. “Create six presentation slides based on this paper.”
5. “Generate ten viva questions with easy answers.”

Choose a result tab, open **Paper evidence**, and inspect **Agent Activity**. Slides have a PowerPoint download. Viva answers can be revealed one at a time or all together.

## Architecture

PyMuPDF extracts page text and LangChain splits it into overlapping chunks. Sentence Transformers MiniLM embeds chunks and queries. A document-specific ChromaDB collection returns nearby excerpts. A shared `ChatOllama` model uses separate LangChain prompts to route, decide whether to search, and generate a task result. Pydantic validates the returned JSON and python-pptx writes editable slides. Streamlit holds the current paper and conversation.

## Verification

```bash
python -m pytest -m "not live" -q
python -m pytest -m live -s
```

The first command tests parsing, Chroma mechanics with controlled vectors, mocked orchestration, and real PowerPoint serialization. The second requires both model setups and verifies genuine retrieval and generation. Set `PAPERPILOT_DEMO_PPTX` to an output path to save the live deck. See the [acceptance checklist](docs/ACCEPTANCE_CHECKLIST.md) for measured results and the [demo guide](docs/DEMO_GUIDE.md) for the browser walkthrough.

## Troubleshooting

- **Ollama unavailable.** Check `ollama list`, then click **Refresh connection**. Open the Ollama desktop app or start `ollama serve`.
- **Ollama stalls during GPU initialization.** For a CPU-only NVIDIA workaround on Windows, exit the Ollama desktop app, set `$env:CUDA_VISIBLE_DEVICES='-1'` and `$env:OLLAMA_VULKAN='0'` in PowerShell, then run `ollama serve` in that terminal. The Windows test machine used this workaround.
- **No local model listed.** Run the model pull yourself, then refresh. The app performs zero automatic model downloads.
- **Embedding model unavailable.** Run `python -m sample_data.setup_embeddings` using the same `HF_HOME`. Restart the app or retry the upload.
- **Unreadable PDF.** Open the file locally. For a scan, OCR it first and upload the text-based copy. For a locked paper, upload an unlocked copy you can access.
- **Bad structured response.** Use a focused request, use a quick action for a known task, or try a stronger installed model. Retry after checking Ollama if it stopped mid-request.
- **No evidence.** Try a named section or term and inspect the retrieved excerpts.
- **Upload limit.** The default is 20 MB. Set `PAPERPILOT_MAX_UPLOAD_MB` and match `server.maxUploadSize` in `.streamlit/config.toml` if you need a different limit.

## Limitations

One active text-based paper per session. Figures, tables, formulas, and complex reading order can lose meaning during text extraction. Semantic retrieval can miss relevant passages. Page validation confirms the page was supplied to the model. Review the excerpts for factual support. Model speed and JSON compliance depend on the selected model and computer. The in-memory Chroma collection and UI history are temporary.

## Academic material

- [Architecture](docs/ARCHITECTURE.md)
- [Project folder tree](docs/FILE_TREE.md)
- [Code walkthrough](docs/CODE_WALKTHROUGH.md)
- [Project report](docs/PROJECT_REPORT.md)
- [Demo script](docs/DEMO_GUIDE.md)
- [Viva guide and quick revision](docs/VIVA_GUIDE.md)
- [FAIR sample attribution](sample_data/README.md)
