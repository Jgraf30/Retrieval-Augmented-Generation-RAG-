import os, json
from rag import build_store, Store, answer

def test_end_to_end(tmp_path):
    data = tmp_path/"data"
    store = tmp_path/"store"
    os.makedirs(data, exist_ok=True)
    with open(data/"doc.txt", "w", encoding="utf-8") as f:
        f.write("Contoso builds secure Microsoft 365 solutions. External sharing is restricted.")

    st = build_store(str(data), str(store), chunk_size=20, overlap=5)
    assert len(st.meta) > 0

    res = answer(Store.load(str(store)), "What does Contoso build?", k=3)
    assert "Contoso" in json.dumps(res)
