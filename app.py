import os
from fastapi import FastAPI
from pydantic import BaseModel
from rag import Store, build_store, answer

app = FastAPI(title="RAG API")
STORE_DIR = os.getenv("STORE_DIR", "store")
DATA_DIR  = os.getenv("DATA_DIR", "data")

class AskReq(BaseModel):
    q: str
    k: int = 5

@app.post("/ingest")
def ingest():
    st = build_store(DATA_DIR, STORE_DIR)
    return {"status": "ok", "chunks": len(st.meta)}

@app.post("/ask")
def ask_api(body: AskReq):
    st = Store.load(STORE_DIR)
    res = answer(st, body.q, k=body.k)
    return res
