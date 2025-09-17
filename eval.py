import argparse, json
from rag import Store, answer

SAMPLE = [
    {"q": "What does Contoso build?", "must_include": ["Contoso"]},
    {"q": "Is external sharing mentioned?", "must_include": ["sharing","share"]},
]

def run_eval(store_dir: str, suite: str = "sample"):
    st = Store.load(store_dir)
    cases = SAMPLE
    results = []
    for c in cases:
        res = answer(st, c["q"], k=5)
        passed = all(m.lower() in res["answer"].lower() for m in c["must_include"] if m)
        results.append({"q": c["q"], "passed": passed, "answer": res["answer"]})
    print(json.dumps({"results": results}, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--suite", default="sample")
    args = ap.parse_args()
    run_eval(args.store, suite=args.suite)
