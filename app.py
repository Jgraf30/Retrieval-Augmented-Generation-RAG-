from fastapi import FastAPI, Query
from rag import ask, ingest

app = FastAPI(title="RAG API")

@app.get("/ingest")
def ingest_api(data: str = "data", store: str = "store"):
    ingest(data, store)
    return {"status": "ok", "message": f"Ingested docs from {data}"}

@app.get("/ask")
def ask_api(q: str = Query(..., description="Your question"), store: str = "store"):
    ask(store, q)
    return {"status": "ok", "query": q}
