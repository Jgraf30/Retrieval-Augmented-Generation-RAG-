import argparse, json
from rag import Store, build_store, answer

def main():
    ap = argparse.ArgumentParser(description="Run RAG end-to-end and write JSON output")
    ap.add_argument("--data", default="data")
    ap.add_argument("--store", default="store")
    ap.add_argument("--q", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", default="answers.json")
    args = ap.parse_args()

    # Ensure store is built (idempotent)
    st = build_store(args.data, args.store)
    res = answer(Store.load(args.store), args.q, k=args.k)

    out = {
        "question": args.q,
        "top_k": args.k,
        "result": res
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"[DONE] wrote {args.out}")

if __name__ == "__main__":
    main()
