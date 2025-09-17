import os, json
import streamlit as st
from rag import Store, build_store, answer

st.set_page_config(page_title="LLM RAG Starter", page_icon="🔎", layout="wide")
STORE_DIR = os.getenv("STORE_DIR", "store")
DATA_DIR  = os.getenv("DATA_DIR", "data")

st.title("🔎 LLM RAG Starter (Cloud-run friendly)")
st.write("Ingest PDFs/TXT from **data/** and ask questions with citations.")

c1, c2 = st.columns([1,1])
with c1:
    if st.button("📥 Rebuild store"):
        st.info("Building…")
        st.session_state.last_ingest = build_store(DATA_DIR, STORE_DIR)
        st.success(f"Store built. Chunks: {len(st.session_state.last_ingest.meta)}")
with c2:
    if st.button("🔄 Reload store"):
        st.session_state.store = Store.load(STORE_DIR)
        st.toast("Store reloaded", icon="✅")

st.divider()
q = st.text_input("💬 Your question", placeholder="e.g., What does Contoso build?")
k = st.slider("Top-K passages", 1, 10, 5)

if st.button("🧠 Ask") and q.strip():
    st.info("Thinking…")
    st_store = Store.load(STORE_DIR)
    res = answer(st_store, q, k=k)
    st.subheader("Answer")
    st.write(res["answer"])

    st.subheader("Sources")
    if not res["sources"]:
        st.write("_No sources found — try rebuilding the store or adding more docs._")
    else:
        for s in res["sources"]:
            st.markdown(
                f"- **[{s['rank']}]** `{s['source']}` (score {s['score']:.3f}, chars {s['begin']}–{s['end']})"
            )
