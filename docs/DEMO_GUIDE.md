# Teacher demonstration · six minutes

Before class, run the setup in the README, start Ollama and Streamlit, and check the FAIR sample. Keep the generated backup deck handy. Local generation time varies. If a response is still running, explain the next step while it completes.

## 0:00–0:45 · Introduce the problem and index a paper

Say “PaperPilot turns one research paper into study material for a presentation and a viva. The model and vector database run locally.” Show the model selector and connection status. Upload the included `fair-principles.pdf` through the sidebar or use the sample button. Point to pages, indexed chunks, and the ingestion events. This covers the GUI and vector database requirements.

## 0:45–1:35 · Show summary and grounding

Enter “Summarize this paper in simple language.” Show the Summary tab, its sections, and at least one cited page. Open **Paper evidence** and compare the claim with the excerpt. In **Agent Activity**, point out summary intent and Chroma search. This demonstrates live LLM integration and one routed task.

## 1:35–2:25 · Explain and revise

Enter “Explain the methodology and important concepts.” Open **Concepts** and explain that the sample paper reports a framework and workshop process. Enter “Make your previous explanation shorter.” Show the activity event for reusing existing excerpts without querying Chroma. Then ask “What was the exact dollar amount of the authors’ grant from the Martian Science Agency?” Show the insufficiency message and bounded retry. This demonstrates conditional retrieval.

## 2:25–3:30 · Export slides

Enter “Create six presentation slides based on this paper.” Open **Slides**, point to the title and conclusion, and click **Download PowerPoint**. Open the file and show a source footer. Mention that Pydantic checks the slide data and python-pptx writes the file.

## 3:30–4:30 · Practice the viva

Enter “Generate ten viva questions with easy answers.” Open **Viva**, read one question, and reveal its suggested answer. Show the difficulty and page reference. Point to the agent selection event.

## 4:30–6:00 · Show prompts, LCEL, and acceptance evidence

Open **How this request was processed**. Show the router's few-shot examples, a zero-shot task prompt, the system and user roles, and structured JSON. Open `core/llm.py` to point out the actual LCEL expression. Use the acceptance checklist to identify evidence for each criterion. If time permits, clear conversation and ask “Explain the comparison.” The app should ask which comparison the student means.

## Backup

If Ollama stops, show the connection status, check `ollama list`, start Ollama, and refresh. If generation is unavailable, demonstrate PDF indexing if MiniLM is ready and open `demo/FAIR-demo.pptx` from the submission ZIP. Introduce it as an earlier real-model export. Use the acceptance checklist to identify previously verified features.
