#!/usr/bin/env python3
import json, pathlib

OUT = pathlib.Path("questions.json")

def default_questions():
    return [
        "What does the documentation say?",
        "Summarize the key points.",
        "What are the main findings?",
        "List the top 5 takeaways.",
        "What recommendations are provided?"
    ]

def main():
    # If questions.json already exists and is valid, don’t overwrite
    if OUT.exists():
        try:
            q = json.loads(OUT.read_text(encoding="utf-8"))
            if isinstance(q, list) and q:
                print("Using existing questions.json")
                return
        except Exception:
            pass

    qs = default_questions()
    OUT.write_text(json.dumps(qs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(qs)} question(s).")

if __name__ == "__main__":
    main()
