# LLM RAG Starter

A minimal Retrieval-Augmented Generation system:
- Ingest PDFs/TXT into a local vector store
- Ask questions; get grounded answers with citations
- Streamlit UI and FastAPI API
- Works **without** an API key (deterministic demo embeddings), or with OpenAI for quality

## Quick Start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Optional: use real models
# export OPENAI_API_KEY=sk-...

# 1) Put PDFs/TXT into ./data
mkdir -p data && cp your.pdf data/

# 2) Build vector store
python rag.py ingest --data data --store store

# 3) Ask via CLI
python rag.py ask --store store --q "What is the main finding?"

# 4a) Run API
uvicorn app:app --reload

# 4b) Run Streamlit UI
streamlit run ui.py
