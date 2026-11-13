# Project folder

```text
PaperPilot-AI/
├── .gitignore
├── .streamlit/config.toml
├── app.py
├── config.py
├── requirements.txt
├── pytest.ini
├── README.md
├── demo/FAIR-demo.pptx  (in the submission ZIP)
├── core/
│   ├── llm.py
│   ├── pdf_processor.py
│   ├── schemas.py
│   ├── vector_store.py
│   └── workflow.py
├── prompts/templates.py
├── utils/pptx_export.py
├── sample_data/
│   ├── fair-principles.pdf
│   ├── README.md
│   └── setup_embeddings.py
├── tests/
│   ├── conftest.py
│   ├── test_export.py
│   ├── test_live.py
│   ├── test_pdf_and_index.py
│   └── test_workflow.py
└── docs/
    ├── ACCEPTANCE_CHECKLIST.md
    ├── ARCHITECTURE.md
    ├── CODE_WALKTHROUGH.md
    ├── DEMO_GUIDE.md
    ├── FILE_TREE.md
    ├── PROJECT_REPORT.md
    └── VIVA_GUIDE.md
```

The four agents are four task entries in `prompts/templates.py` and `core/workflow.py`. They share the structured-call helper and the selected Ollama model.
