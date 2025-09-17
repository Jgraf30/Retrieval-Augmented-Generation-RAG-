import os, json, argparse, hashlib, re
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from pypdf import PdfReader

# Optional OpenAI; code works without it (fallback path)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
GEN_MODEL   = os.getenv("GEN_MODEL", "gpt-4o-mini")

STORE_DIR_DEFAULT = "store"
DATA_DIR_DEFAULT  = "data"

def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _split_chunks(text: str, chunk_size=900, overlap=150) -> List[str]:
    words = text.split()
    if not words: return []
    chunks, i = [], 0
    step = max(chunk_size - overlap, 1)
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        i += step
    return chunks

def _hash_vec(s: str, dim=384) -> np.ndarray:
    """Deterministic fake embedding so runs work without API key."""
    h = hashlib.sha256(s.encode("utf-8")).digest()
    rs = np.random.RandomState(int.from_bytes(h[:4], "little", signed=False))
    v = rs.rand(dim).astype("float32")
    v = v / (np.linalg.norm(v) + 1e-9)
    return v

def _embed_fallback(texts: List[str]) -> np.ndarray:
    return np.stack([_hash_vec(t) for t in texts], axis=0) if texts else np.zeros((0,384), dtype="float32")

def _embed_texts(texts: List[str]) -> np.ndarray:
    """Try OpenAI; if anything goes wrong, fall back silently."""
    if not texts:
        return np.zeros((0,384), dtype="float32")

    use = os.getenv("USE_OPENAI", "auto").lower()
    key = os.getenv("OPENAI_API_KEY", "").strip()

    if use in ("never", "false", "0"):
        return _embed_fallback(texts)

    if OpenAI and key:
        try:
            client = OpenAI()  # reads key from env
            resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
            vecs = np.array([np.array(e.embedding, dtype="float32") for e in resp.data])
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
            return vecs / norms
        except Exception as e:
            print(f"[WARN] OpenAI embeddings failed: {e} → falling back.")
            return _embed_fallback(texts)

    # No SDK or no key → fallback
    return _embed_fallback(texts)

@dataclass
class Store:
    vectors: np.ndarray
    meta: List[Dict]

    @classmethod
    def load(cls, path: str) -> "Store":
        os.makedirs(path, exist_ok=True)
        vec_path = os.path.join(path, "vectors.npz")
        meta_path = os.path.join(path, "meta.json")
        if not (os.path.exists(vec_path) and os.path.exists(meta_path)):
            return cls(np.zeros((0,384), dtype="float32"), [])
        arr = np.load(vec_path)["arr_0"]
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return cls(arr, meta)

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        np.savez_compressed(os.path.join(path, "vectors.npz"), self.vectors)
        with open(os.path.join(path, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

    def search(self, query: str, k: int = 5) -> List[Tuple[float, Dict]]:
        if len(self.meta) == 0: return []
        qv = _embed_texts([query])[0]
        sims = (self.vectors @ qv)  # normalized → cosine == dot
        idx = np.argsort(-sims)[:k]
        return [(float(sims[i]), self.meta[i]) for i in idx]

def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    out = []
    for p in reader.pages:
        out.append(p.extract_text() or "")
    return "\n".join(out)

def _load_docs(data_dir: str) -> List[Tuple[str,str]]:
    docs = []
    for root, _, files in os.walk(data_dir):
        for fn in files:
            fp = os.path.join(root, fn)
            if fn.lower().endswith(".txt"):
                docs.append((fp, _read_txt(fp)))
            elif fn.lower().endswith(".pdf"):
                docs.append((fp, _read_pdf(fp)))
    return docs

def build_store(data_dir: str, store_dir: str, chunk_size=900, overlap=150) -> 'Store':
    docs = _load_docs(data_dir)
    metas, texts = [], []
    for src, raw in docs:
        text = _normalize_ws(raw)
        if not text: continue
        chunks = _split_chunks(text, chunk_size=chunk_size, overlap=overlap)
        off = 0
        for ch in chunks:
            begin = off
            end = off + len(ch)
            off = end
            metas.append({
                "id": hashlib.md5((src+str(begin)).encode()).hexdigest()[:10],
                "source": os.path.relpath(src, start=data_dir),
                "chunk": ch,
                "begin": begin,
                "end": end
            })
            texts.append(ch)
    if not texts:
        store = Store(np.zeros((0,384), dtype="float32"), [])
        store.save(store_dir)
        return store
    vecs = _embed_texts(texts)
    store = Store(vecs, metas)
    store.save(store_dir)
    return store

SYSTEM_PROMPT = """You are a concise assistant. Answer USING ONLY the provided context chunks.
Cite sources as [n] for the provided chunk index. If not in the chunks, say you don't know.
"""

def _llm_answer(question: str, contexts: List[str]) -> str:
    use = os.getenv("USE_OPENAI", "auto").lower()
    key = os.getenv("OPENAI_API_KEY", "").strip()

    if use in ("never", "false", "0"):
        return (" ".join(contexts[:2])[:1200] if contexts else "I don't know.")

    if OpenAI and key:
        try:
            client = OpenAI()
            msgs = [
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content": f"Question: {question}\n\nContext:\n" + "\n\n".join(f"[{i+1}] {c}" for i,c in enumerate(contexts))}
            ]
            resp = client.chat.completions.create(model=GEN_MODEL, messages=msgs, temperature=0.2)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] OpenAI chat failed: {e} → falling back.")

    # Fallback: extractive (top chunks)
    return (" ".join(contexts[:2])[:1200] if contexts else "I don't know.")

def answer(store: 'Store', q: str, k: int = 5) -> Dict:
    hits = store.search(q, k=k)
    contexts = [h[1]["chunk"] for h in hits]
    answer_text = _llm_answer(q, contexts)
    return {
        "question": q,
        "answer": answer_text,
        "sources": [
            {"rank": i+1, "score": float(score), "source": h["source"], "begin": h["begin"], "end": h["end"]}
            for i,(score,h) in enumerate(hits)
        ]
    }

def main():
    ap = argparse.ArgumentParser(description="RAG minimal (cloud-friendly)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="ingest PDFs/TXT from data/ into store/")
    p_ing.add_argument("--data", default=DATA_DIR_DEFAULT)
    p_ing.add_argument("--store", default=STORE_DIR_DEFAULT)
    p_ing.add_argument("--chunk_size", type=int, default=900)
    p_ing.add_argument("--overlap", type=int, default=150)

    p_ask = sub.add_parser("ask", help="ask a question against the store")
    p_ask.add_argument("--store", default=STORE_DIR_DEFAULT)
    p_ask.add_argument("--q", required=True)
    p_ask.add_argument("--k", type=int, default=5)

    args = ap.parse_args()
    if args.cmd == "ingest":
        st = build_store(args.data, args.store, chunk_size=args.chunk_size, overlap=args.overlap)
        print(f"[INGEST] chunks: {len(st.meta)} → {args.store}")
    elif args.cmd == "ask":
        st = Store.load(args.store)
        out = answer(st, args.q, k=args.k)
        print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
