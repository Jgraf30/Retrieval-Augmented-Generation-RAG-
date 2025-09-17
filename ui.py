import os, json
import streamlit as st
from rag import Store, build_store, answer

st.set_page_config(page_title="LLM RAG Starter", layout="wide")
STORE_DIR = os.getenv("STORE_DIR", "store")
DATA_DIR  = os.getenv("DATA_DIR", "data")

st.title("🔎 LLM RAG Starter")
st.write("Ingest PDFs/TXT from **data/** and ask questions with citations.")

col1, col2 = st.columns(2)
with col1:
    if st.button("📥 Rebuild store from ./data"):
        st.info("Building…")
        st.session_state.last_ingest = build_store(DATA_DIR, STORE_DIR)
        st.success(f"Store built. Chunks: {len(st.session_state.last_ingest.meta)}")

with col2:
    st.download_button(
        "⬇️ Download metadata (if exists)",
        data=json.dumps(Store.load(STORE_DIR).meta, indent=2),
        file_name="meta.json",
        mime="application/json"
    )

q = st.text_input("Your question")
k = st.slider("Top K passages", min_value=1, max_value=10, value=5)
if st.button("🧠 Ask") and q.strip():
    st.info("Thinking…")
    st_store = Store.load(STORE_DIR)
    res = answer(st_store, q, k=k)
    st.subheader("Answer")
    st.write(res["answer"])

    st.subheader("Sources")
    for s in res["sources"]:
        st.markdown(f"- **[{s['rank']}]** `{s['source']}` (score {s['score']:.3f}, {s['begin']}–{s['end']})")
