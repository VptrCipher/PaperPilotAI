# PaperPilot AI
## Assignment 5 · Paper-to-Presentation & Viva Agent

### Abstract

PaperPilot AI is a local academic assistant that converts a text-based research paper into a structured summary, explanations, editable PowerPoint slides, and oral-exam practice. It combines local semantic search with a shared instruction model and four task-specific LangChain prompts. The application shows retrieved excerpts and processing events so students can inspect the evidence and explain the system.

### 1. Introduction

Reading a paper involves identifying its problem, methods, contribution, findings, and limitations. A presentation also requires selecting material for slides, and a viva requires being able to explain that material in one's own words. PaperPilot brings these preparation tasks into one workspace.

### 2. Problem statement

Students may spend substantial time locating important passages and turning them into study material. A generated explanation can also be difficult to check when it omits its source. The application aims to speed up preparation while keeping each document-specific output traceable to paper excerpts.

### 3. Objectives

Accept a research PDF, extract text with page information, and build a local semantic index. Route natural-language requests to four agents, decide when evidence should be retrieved, and return task-specific output with source pages. Export an editable PowerPoint and let students reveal viva answers after attempting questions.

### 4. Existing approach

A manual workflow uses a PDF reader, notes, and a presentation editor. Keyword search can locate familiar phrases. Basic retrieval-augmented generation can find passages by meaning and supply them to a model. A workflow that retrieves for every turn may repeat work during a straightforward revision.

### 5. Proposed system

PaperPilot supports one active paper. The user chooses an installed local model, uploads a PDF, and uses a quick action or writes a request. The route determines the task. The retrieval decision chooses between searching, reusing evidence, and clarification. Validation and source previews help users inspect the result.

### 6. Technology stack

Python handles the workflow. Streamlit provides the browser interface. PyMuPDF reads the paper. LangChain provides the text splitter, prompts, parsers, and LCEL. Ollama runs Qwen2.5 locally through ChatOllama. Sentence Transformers supplies MiniLM embeddings. Chroma stores the vectors. Pydantic validates structured data, python-pptx creates the deck, and pytest exercises the project.

### 7. System architecture

The document pipeline is PDF → page text → chunks → embeddings → Chroma. The request pipeline is GUI → route → retrieval decision → selected task → validation → display or export. See [Architecture](ARCHITECTURE.md) for diagrams and component boundaries.

### 8. Agent design

The Summarizer Agent fills eight research sections. The Concept-Extractor Agent answers methodology and terminology questions and can label requested general background. The Slide-Generator Agent structures supported material into a five-to-ten-slide deck. The Viva Agent prepares questions, suggested answers, and difficulty levels. All four use the same local LLM.

### 9. Agentic RAG implementation

The system can search Chroma, reuse previously retrieved material for a revision, or ask a clarifying question. Broad retrieval looks across paper topics, while focused requests use a targeted query. After one additional targeted search, unresolved evidence results in an explicit insufficiency message. The excerpt budget and retry limit keep the workflow bounded.

### 10. Intent routing

A few-shot prompt classifies the latest request using a short conversation history. Pydantic validates intent, count, difficulty, scope, and revision status. Quick actions provide a direct route. A follow-up can inherit the task from the previous output.

### 11. Implementation

A file hash controls re-indexing. Chroma stores page and chunk identifiers with each embedding. Task prompts use research excerpts as data and instruct the model to cite only supporting pages. The workflow checks cited pages against supplied excerpts. Streamlit displays the schema-backed output and builds the deck from the same data used in the slide preview.

### 12. Testing and results

PDF, collection isolation, conditional workflow, schema checks, and file export are covered by automated tests. The final Windows run passed 20 deterministic tests and two live tests using the bundled FAIR paper, MiniLM, Chroma, and Qwen2.5 through Ollama. Ubuntu 24.04 under WSL passed 20 deterministic tests. Chrome verified upload, a live summary, and PowerPoint download. Microsoft PowerPoint opened and rendered the six-slide demo. The [acceptance checklist](ACCEPTANCE_CHECKLIST.md) maps the results to the seven criteria.

### 13. Advantages

A student can use ordinary language, trace citations back to excerpts, revise a response without repeated retrieval when evidence suffices, and work locally after setup. The code uses a small number of components that can be explained individually in a viva.

### 14. Limitations

The system does not read scanned pages without prior OCR. Extraction may lose column order or table and figure relationships. A small model can misclassify intent or misread a passage. Page-membership validation cannot establish that every claim is supported. The demo measures operation on one sample and gives no estimate of overall accuracy.

### 15. Future scope

Possible extensions include OCR, better table and figure handling, a comparison mode for multiple papers, and evidence evaluation on a diverse set of research papers.

### 16. Conclusion

PaperPilot demonstrates a local workflow from research paper to study and presentation material. The route, retrieval actions, task prompts, and source excerpts are visible for demonstration and review.

### 17. References

- Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3, 160018. [DOI](https://doi.org/10.1038/sdata.2016.18)
- Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 33*. [Proceedings](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html)
- [LangChain Python documentation](https://docs.langchain.com/oss/python/langchain/overview)
- [Ollama documentation](https://docs.ollama.com/)
- [MiniLM embedding model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [Chroma documentation](https://docs.trychroma.com/)
- [Streamlit documentation](https://docs.streamlit.io/)
- [python-pptx documentation](https://python-pptx.readthedocs.io/)
