# PaperPilot AI viva guide

Read each answer aloud, then point to the matching feature or file. The examples assume the included FAIR paper unless stated otherwise.

## A · Project basics

### 1. What is PaperPilot AI?

A local academic assistant that turns one research PDF into summaries, explanations, slides, and oral-exam practice.

### 2. What problem does the project solve?

Students must find the important passages in a paper and turn them into several different study formats. PaperPilot gathers evidence and prepares those formats in one workspace.

### 3. Who is it for?

Students preparing presentations and vivas, and instructors who want to show how model outputs can be traced to paper excerpts.

### 4. Why did you choose this project?

The task has a clear input, four distinct outputs, and a practical reason to choose when to search for evidence.

### 5. What are the four main features?

A structured summary, concept explanations, an editable PowerPoint deck, and a viva practice view.

### 6. What is the main limitation?

It supports one text-based paper at a time, and both the extracted text and the generated claims need review.

### 7. What is the demo paper?

An open-access Scientific Data Comment by Wilkinson and colleagues introducing the FAIR Guiding Principles. It describes a workshop and principles, so I would avoid calling it a controlled experiment.

## B · Agentic AI fundamentals

### 8. What is AI?

AI is the field of building systems that perform tasks such as recognition, prediction, or language understanding.

### 9. What is Generative AI?

It produces new content from learned patterns. In this app the model writes summaries, explanations, slides, and viva answers.

### 10. What is Agentic AI?

An agentic system chooses among actions to achieve a goal. Here the local model helps decide whether to search, reuse excerpts, or ask a question.

**In PaperPilot:** A shorter-explanation request can reuse the excerpts already in memory.

**Examiner follow-up:** Where does the action happen? run_request branches on turn.action in core/workflow.py.

### 11. What is an agent?

A component that takes input, has a defined goal or role, and can contribute an action or result in a workflow.

### 12. How does this differ from a simple chatbot?

A paper request can lead to a database search and a validated slide export. The action depends on the task and available evidence.

### 13. What does autonomy mean in this app?

The workflow can act on a validated retrieval decision within a fixed set of actions and retry limits.

### 14. What is orchestration?

It is the order and coordination of routing, retrieval, task generation, validation, and display.

### 15. What is the role of tools?

Chroma search supplies evidence, and the PowerPoint exporter converts validated slide data into a usable file.

### 16. What is a multi-agent system here?

Four task-specialized prompt and schema pairs provide distinct roles inside one application.

### 17. Why share one model?

The prompts and schemas define the roles. Sharing one Ollama model keeps setup and memory requirements manageable.

## C · LLM fundamentals

### 18. What is an LLM?

A large language model predicts text tokens conditioned on a context. An instruction-tuned model can use those predictions to answer requests.

### 19. What is a token?

A unit the model reads or produces, often a word fragment or punctuation. Character count is only an approximation of token count.

### 20. What is a context window?

The amount of input and generated text a model can hold for one call. The app requests an 8,192-token window and caps excerpt text.

### 21. What is a prompt?

The messages supplied to the model, including role instructions, the request, and any evidence.

### 22. What is an instruction-following model?

A model adapted to respond to directions such as writing an eight-section summary or emitting JSON.

### 23. What is inference?

Running an already trained model to produce an output from an input.

### 24. What is temperature?

A sampling setting that influences variation. The app requests zero temperature to favor consistency.

### 25. What is hallucination?

A fluent model claim that lacks factual support. It can still occur when excerpts are provided.

### 26. What is Ollama?

The runtime serving the locally installed instruction model over an HTTP interface on this computer.

**In PaperPilot:** The sidebar lists installed local models via the Ollama API.

**Examiner follow-up:** Can four agents use it concurrently? The project uses sequential calls for one request. Each task uses the selected shared model.

### 27. How do local and cloud models differ?

Local inference uses this computer's resources. Cloud inference uses a remote provider and requires sending the request over a network.

### 28. Did you train a model?

I use pretrained Qwen2.5 and MiniLM weights. The project changes their inputs and validates their outputs.

### 29. Why choose Qwen2.5 3B?

It is a small instruction model suitable for a local demo and supports the structured generation approach used here.

## D · Prompt engineering

### 30. What is prompt engineering?

Designing and evaluating model instructions, inputs, examples, and output requirements for a task.

### 31. What is a system prompt?

A message that defines the role, rules, and expected response behavior.

### 32. What is a user prompt?

The message containing the current task and inputs, such as the request and excerpts.

### 33. What is zero-shot prompting?

Giving instructions without example input-output exchanges. The four task templates use this technique.

### 34. What is few-shot prompting?

Including a few example inputs and desired outputs. The intent router shows a viva request and a revision.

**In PaperPilot:** The route prompt includes an example asking for eight beginner viva questions.

**Examiner follow-up:** How is the slide agent prompted? It uses instructions and an output schema. See prompts/templates.py.

### 35. Why separate the prompts?

Each task has a different goal and output shape. A slide prompt prioritizes short bullets, while a viva prompt writes questions and answers.

### 36. What is structured output?

Data that conforms to a known shape, such as a list of slides containing titles, bullets, and page numbers.

**In PaperPilot:** A slide item has title, bullets and source_pages fields.

**Examiner follow-up:** What if the JSON is malformed? structured_call retries once with format feedback, then reports an error.

### 37. What is ReAct?

A general approach that interleaves model decisions and tool observations. This project uses a simpler explicit branching workflow.

### 38. What is reflection?

Reviewing or critiquing a candidate result before revising it. Here the retry provides validation feedback about format or constraints.

### 39. What is chain-of-thought prompting?

A technique concerned with intermediate reasoning in model outputs. This app records observable actions and brief task labels.

### 40. Which prompt techniques are implemented?

System and user roles, few-shot examples for routing, instruction-based zero-shot task prompts, and JSON schema constraints.

## E · RAG and Agentic RAG

### 41. What is RAG?

Retrieval-augmented generation supplies the model with relevant external evidence before generation.

**In PaperPilot:** MiniLM encodes a query about FAIR principles, Chroma returns related passages, and the agent sees them with page numbers.

**Examiner follow-up:** Does it train on the paper? The text is supplied at inference time through the prompt.

### 42. Why is RAG necessary here?

The paper may be absent from model training, and the user needs answers tied to the uploaded version and its page numbers.

### 43. What are the main RAG stages?

Extract and index content, retrieve relevant passages for a question, then generate an answer using those passages.

### 44. What is Agentic RAG?

A retrieval workflow that can make a decision about whether and how to retrieve based on the request and current evidence.

**In PaperPilot:** A new factual question searches Chroma. A simple revision can reuse evidence.

**Examiner follow-up:** How is it bounded? One routing decision, one retrieval decision, and at most one additional evidence search after insufficient output.

### 45. How does this differ from an always-retrieve pipeline?

A shortening request can reuse excerpts and skip Chroma. An ambiguous request can ask for clarification first.

### 46. When do you retrieve?

When the request asks for new facts, when the decision calls for search, or when a permitted reuse lacks cached evidence.

### 47. When do you reuse context?

When the router identifies a revision, the decision selects reuse, and the last completed turn supplies current-paper excerpts.

### 48. What happens when the PDF lacks the answer?

An insufficient result can trigger one targeted search. If evidence remains insufficient, the user receives an explicit message.

**In PaperPilot:** Ask for the exact amount of a Martian Science Agency grant in the FAIR paper.

**Examiner follow-up:** What does the application show? The workflow reports insufficient evidence and lets the user inspect the excerpts.

### 49. How does RAG reduce hallucination?

It gives the model source material and asks for supporting pages. The application rejects references to pages outside the supplied excerpts.

### 50. Can RAG guarantee factual correctness?

No. Search can miss a relevant passage, and a model can misinterpret or incorrectly cite evidence.

**In PaperPilot:** A real PDF page number may still be cited for an unsupported claim.

**Examiner follow-up:** How do I check the claim? Read the source excerpt and the original page. Page checks enforce membership in the supplied evidence.

### 51. What are citations?

References that help a reader find the evidence for a claim. Here they are physical PDF page numbers.

### 52. Why retain page metadata?

It lets users verify claims against the actual PDF and shows which page a retrieved chunk came from.

## F · Embeddings and vector databases

### 53. What is an embedding?

A vector of numbers produced by a model to represent text for comparison.

**In PaperPilot:** The same MiniLM encoder represents both a FAIR excerpt and a search query.

**Examiner follow-up:** Can you read the meaning of one vector coordinate? The representation is distributed across dimensions. See core/vector_store.py.

### 54. Why convert text into vectors?

A similarity measure can compare related phrases even when their exact wording differs.

### 55. What is semantic similarity?

Closeness in meaning. For example, ‘how can I find a dataset?’ can retrieve content about findability.

### 56. What is a vector database?

A database that stores vectors with data or metadata and supports queries for nearby vectors.

### 57. What is ChromaDB?

The local database used to store and search the current paper's embeddings and excerpts.

### 58. How does Chroma differ from a relational database?

Chroma centers on similarity search and metadata. A relational system centers on tables, SQL, and relationships, although it can also be extended for vectors.

### 59. What is similarity search?

Embed the query and rank stored vectors by distance in the same vector space.

### 60. What is cosine similarity?

The cosine of the angle between two vectors. It is their dot product divided by the product of their lengths. A smaller angle means greater similarity.

**In PaperPilot:** Related phrases can point in similar directions even if the exact words differ.

**Examiner follow-up:** What if a top result is unrelated? The agent can report insufficient evidence. Similarity gives a ranking.

### 61. What is chunking?

Splitting long text into smaller passages so retrieval can pick useful excerpts.

### 62. What is overlap?

Some nearby text can appear in adjacent chunks, which helps preserve sentences or ideas split by a boundary.

### 63. What is top-k retrieval?

Return up to k nearby chunks. The app requests five for a targeted query and two per query for broad retrieval.

### 64. Why encode queries and chunks with the same model?

Vectors must have compatible dimensions and meanings so their distances are interpretable.

### 65. How does MiniLM differ from Qwen?

MiniLM outputs search vectors. Qwen produces language and structured task decisions.

### 66. Does a nearby vector prove the answer is present?

No. A search can return the closest passage even when the answer is absent. The agent must evaluate its evidence.

## G · LangChain and LCEL

### 67. What is LangChain?

A library of components for model calls, prompts, parsers, and other pieces of language-model workflows.

### 68. Why is LangChain used?

It makes prompt roles and the model/parser pipeline explicit and satisfies the assignment's LCEL requirement.

### 69. What is LCEL?

LangChain Expression Language composes runnable components into a chain with the pipe operator.

**In PaperPilot:** The exact chain is `chain = prompt | model | StrOutputParser()`, where `model = llm.bind(format=schema.model_json_schema())`.

**Examiner follow-up:** Where is JSON parsed? `schema.model_validate_json(raw)` in core/llm.py.

### 70. What is a prompt template?

A reusable set of messages with named placeholders filled at runtime.

### 71. What is an output parser?

A component that extracts or converts a model response. StrOutputParser returns text, then Pydantic validates the JSON.

### 72. What does the pipe do?

It passes the formatted messages to the model and passes the model response to the parser.

### 73. What does invoke do?

It executes the runnable once with a supplied input dictionary and returns its result.

### 74. What is a chain?

An ordered composition of operations. In the project each structured model call uses an LCEL chain.

### 75. How does an agent differ from a chain?

The chain is one way to perform a call. The wider workflow uses outputs from those calls to choose and execute actions.

### 76. How does LangChain connect to Ollama?

ChatOllama uses the Ollama client to send chat messages and a JSON schema to the loopback service.

## H · Intent detection and routing

### 77. What is intent?

The task a user wants to accomplish, such as making slides or preparing for an exam.

### 78. What is intent detection?

Classifying a request into a supported task using the language of the request and recent context.

### 79. What is routing?

Using that classification to choose a task prompt, return app help, or ask for clarification.

### 80. How does the app detect intent?

A few-shot prompt sends the request and recent turns to the local model, then Pydantic validates the returned route.

**In PaperPilot:** A request for examiner practice maps to viva with a count and difficulty.

**Examiner follow-up:** What if the model returns an unknown value? Validation allows one correction attempt and then presents an error. See core/schemas.py and core/llm.py.

### 81. What if the route is valid but wrong?

The selected agent can answer the wrong task. The user can inspect the route in Agent Activity and rephrase or use a quick action.

### 82. How does it understand follow-ups?

It receives recent requests and the last completed task. The retrieval and task prompts can use the previous output for a revision.

### 83. What happens with an ambiguous request?

The router or retrieval decision can ask which topic or comparison the user means.

### 84. Why include both natural language and buttons?

Natural language supports custom requests and follow-ups. Buttons are a direct path to a known task and its controls.

## I · Implementation and practical questions

### 85. Why Python?

Its ecosystem supplies the PDF, embedding, vector database, model, UI, and testing libraries used here.

### 86. Why Streamlit?

It builds the required interactive browser interface using Python widgets and keeps a simple application state.

### 87. How is text extracted?

PyMuPDF opens PDF bytes and returns page text. The application processes pages independently and recognizes common section headings.

### 88. What is PyMuPDF?

A Python interface to MuPDF that can open and extract text from PDF pages.

### 89. How do you make a PowerPoint?

Validate a Slides object, create editable text boxes and slide footers with python-pptx, then save to a BytesIO buffer.

**In PaperPilot:** The FAIR deck uses the same slide titles and bullets shown in the app.

**Examiner follow-up:** What happens if the model emits eleven slides? Pydantic and validate_answer reject the count before build_pptx runs.

### 90. What is session state?

Streamlit's per-session memory across reruns. It stores the active index, recent turns, activity, and exports.

### 91. What happens when a new PDF is uploaded?

A changed SHA-256 digest causes the active collection to be cleared and conversation state to reset before the replacement is indexed.

### 92. How do you prevent document mixing?

Each active collection has a unique name, and workflow history is filtered by the active paper hash.

**In PaperPilot:** Replacing the sample paper clears its collection and conversation.

**Examiner follow-up:** What if old history is passed to run_request? The workflow filters history by document_id before considering reuse.

### 93. What happens when a file is invalid or missing?

Invalid inputs get an upload error. Paper-specific requests without an active index prompt the user to upload a PDF.

### 94. What happens if Ollama stops?

The request fails with a connection or local-processing message. The user can restart Ollama and refresh the connection.

### 95. Does it need internet?

Setup downloads dependencies and weights. After setup the embedder reads local files and the model request uses loopback.

### 96. Does the app send paper data to a remote server?

The app uses a loopback model endpoint and an in-process index, disables tracing and optional usage telemetry, and loads the embeddings locally.

### 97. How did you test the application?

Deterministic tests check extraction, Chroma mechanics, routing branches and file structure. The opt-in live suite uses the actual paper and both models. The checklist records measured results.

### 98. What could improve the system?

OCR, table and figure understanding, stronger evidence evaluation, and support for comparing multiple papers.

### 99. Why does a same-file rerun avoid re-indexing?

The app computes a hash of the raw bytes and checks it against the active paper before extracting and embedding again.

### 100. How can a student verify a citation?

Open Paper evidence, locate the excerpt by page and chunk, then compare it with the original PDF.

## Questions That Could Confuse You During the Viva

- **Agentic AI and Generative AI.** Generative AI produces content. Agentic behavior chooses which action to take. PaperPilot uses both.
- **Agent and chain.** LCEL executes a prompt-model-parser sequence. The application uses validated outputs to choose actions and one of four task roles.
- **RAG and Agentic RAG.** Both can ground answers in retrieved material. Agentic RAG can search, reuse, or clarify based on context.
- **LLM and embedding model.** Qwen produces text and decisions. MiniLM encodes search vectors.
- **ChromaDB and traditional databases.** Chroma is used for vector similarity and metadata. SQL databases organize relational data and may also support vectors.
- **Prompt engineering and training.** Prompt design changes the inputs. Training changes model weights.
- **Local inference and offline setup.** Ollama inference uses this computer. A fresh install needs dependency and weight downloads.
- **Similarity search and exact search.** Similarity compares meaning using vectors. Exact search compares literal terms or patterns.
- **Model output and verified evidence.** The model proposes an answer and cites supplied pages. A reader checks the source to verify the claim.
- **Four roles and four models.** The four logical agents share one installed model and have separate prompts and structured data.

## Quick revision · 20 questions

1. **What does PaperPilot do?** Turns a PDF into a summary, concepts, slides, and viva practice.
2. **What is the local model?** Qwen2.5 3B through Ollama.
3. **What creates embeddings?** Sentence Transformers all-MiniLM-L6-v2.
4. **What stores them?** A current-paper ChromaDB collection.
5. **What is the retrieval flow?** Embed the query, search vectors, pass excerpts and pages to the agent.
6. **How does it route?** A few-shot LCEL prompt returns a validated intent.
7. **What is LCEL?** Runnable composition with the pipe operator.
8. **What is the actual chain?** Prompt → ChatOllama bound to JSON schema → StrOutputParser.
9. **What validates JSON?** Pydantic plus task-specific count and page checks.
10. **What makes retrieval conditional?** The model chooses retrieve, reuse, or clarify and the workflow executes the action.
11. **When can it reuse?** A revision with relevant excerpts from the current paper.
12. **How many evidence retries?** At most one additional targeted search.
13. **What makes a citation inspectable?** One-based page metadata and an excerpt panel.
14. **What identifies the paper?** SHA-256 of its PDF bytes.
15. **How are papers kept separate?** Unique collection and document-scoped history.
16. **What creates the file?** python-pptx saves a widescreen presentation to bytes.
17. **What is the default viva mix?** Four easy, four intermediate, two advanced.
18. **What happens to a scanned PDF?** It needs a text layer from OCR before upload.
19. **What runs offline?** PDF extraction, embeddings, search, Ollama generation, and export after setup.
20. **What is the key factual limitation?** A supplied page can still be misinterpreted, so check the excerpt.
