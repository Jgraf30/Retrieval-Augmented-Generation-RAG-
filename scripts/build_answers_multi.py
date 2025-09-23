#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, shlex, pathlib

QUESTION_FILE = pathlib.Path("questions.json")
STORE = os.environ.get("STORE", "store")

SRC_RE = re.compile(
    r"^\s*\[(?P<rank>\d+)\]\s+(?P<source>.+?)(?:\s+\(score\s+(?P<score>[0-9.]+)\))?(?:\s+\[(?:begin\s+(?P<begin>\d+))?(?:\s+end\s+(?P<end>\d+))?\])?\s*$",
    re.I
)

def run(cmd: str):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out.strip()

def try_parse_json_payload(text: str, question: str):
    t = text.strip()
    if not t.startswith("{"):
        return None
    try:
        obj = json.loads(t)
    except Exception:
        return None
    answer = (
        obj.get("answer")
        or (obj.get("result") or {}).get("answer")
        or obj.get("output", {}).get("answer")
        or ""
    )
    sources = (
        obj.get("sources")
        or (obj.get("result") or {}).get("sources")
        or []
    )
    norm = []
    if isinstance(sources, list):
        for i, s in enumerate(sources, 1):
            if isinstance(s, dict):
                norm.append({
                    "rank": s.get("rank", i),
                    "score": s.get("score"),
                    "source": s.get("source") or s.get("path") or s.get("id") or "(unknown)",
                    "begin": s.get("begin"),
                    "end": s.get("end"),
                })
            else:
                norm.append({
                    "rank": i,
                    "source": str(s),
                    "score": None,
                    "begin": None,
                    "end": None
                })
    return {
        "question": obj.get("question") or question,
        "answer": str(answer or "").strip(),
        "sources": norm,
        "method": "rag-json",
        "updated_at": int(time.time())
    }

def parse_sources(lines):
    out = []
    for line in lines:
        m = SRC_RE.match(line.strip())
        if m:
            out.append({
                "rank": int(m.group("rank")),
                "score": float(m.group("score")) if m.group("score") else None,
                "source": m.group("source"),
                "begin": int(m.group("begin")) if m.group("begin") else None,
                "end": int(m.group("end")) if m.group("end") else None,
            })
    out.sort(key=lambda x: x["rank"])
    return out

def split_text_and_sources(text: str):
    lines = text.splitlines()
    body_lines = []
    src_lines = []
    in_sources = False
    for raw in lines:
        if not in_sources and re.match(r"^\s*sources\s*:?\s*$", raw, re.I):
            in_sources = True
            continue
        (src_lines if in_sources else body_lines).append(raw)
    if in_sources:
        return "\n".join(body_lines).strip(), parse_sources(src_lines)
    # peel tail
    rev = list(reversed(lines))
    tail = []
    for raw in rev:
        if SRC_RE.match(raw.strip()):
            tail.append(raw)
        else:
            break
    if tail:
        keep = len(lines) - len(tail)
        return "\n".join(lines[:keep]).strip(), parse_sources(reversed(tail))
    return text.strip(), []

def fallback_summary_from_docs(max_chars=1200):
    """Last-resort summary: concatenate first bits of available docs."""
    parts = []
    for ext in ("*.txt", "*.md"):
        for fp in pathlib.Path("data").rglob(ext):
            try:
                t = fp.read_text(encoding="utf-8", errors="ignore").strip()
                if t:
                    parts.append(f"[{fp.name}] {t[:max_chars]}")
                    if sum(len(p) for p in parts) > max_chars:
                        break
            except Exception:
                continue
        if parts:
            break
    if not parts:
        return "No model output and no readable documents found."
    return "Fallback summary (first snippets):\n" + "\n\n".join(parts)[:max_chars]

def answer_one(question: str):
    rc, out = run(f"python rag.py ask --store {shlex.quote(STORE)} --q {shlex.quote(question)}")
    pathlib.Path("last_answer.txt").write_text(out, encoding="utf-8")

    payload = try_parse_json_payload(out, question)
    if not payload:
        body, sources = split_text_and_sources(out)
        payload = {
            "question": question,
            "answer": body or fallback_summary_from_docs(),
            "sources": sources,
            "method": "rag-text" if body else "fallback",
            "updated_at": int(time.time())
        }
    return payload

def main():
    if not QUESTION_FILE.exists():
        print("ERROR: questions.json missing", file=sys.stderr)
        sys.exit(1)
    questions = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
    if not isinstance(questions, list) or not questions:
        print("ERROR: questions.json is empty or invalid", file=sys.stderr)
        sys.exit(1)

    answers = []
    for q in questions:
        print(f"--- Asking: {q}")
        ans = answer_one(q)
        answers.append(ans)

    pathlib.Path("answers_multi.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote answers_multi.json with {len(answers)} entries.")

if __name__ == "__main__":
    main()
