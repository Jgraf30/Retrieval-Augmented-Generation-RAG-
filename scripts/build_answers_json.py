#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, shlex, pathlib

QUESTION = os.environ.get("QUESTION", "What does the documentation say?")
STORE = os.environ.get("STORE", "store")

# Accept both: "[1] path (score 0.777)" and "[1] path (score 0.777) [begin 0 end 6702]"
SRC_RE = re.compile(
    r"^\s*\[(?P<rank>\d+)\]\s+(?P<source>.+?)(?:\s+\(score\s+(?P<score>[0-9.]+)\))?(?:\s+\[(?:begin\s+(?P<begin>\d+))?(?:\s+end\s+(?P<end>\d+))?\])?\s*$",
    re.I
)
SOURCES_HEADER_RE = re.compile(r"^\s*sources\s*:?\s*$", re.I)

def run(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out.strip()

def parse_sources(lines):
    out = []
    for line in lines:
        m = SRC_RE.match(line.strip())
        if not m:
            continue
        rank = int(m.group("rank"))
        source = m.group("source")
        score = float(m.group("score")) if m.group("score") else None
        begin = int(m.group("begin")) if m.group("begin") else None
        end = int(m.group("end")) if m.group("end") else None
        out.append({
            "rank": rank,
            "score": score,
            "source": source,
            "begin": begin,
            "end": end
        })
    out.sort(key=lambda x: x["rank"])
    return out

def split_answer_and_sources(text):
    body_lines, src_lines, in_sources = [], [], False
    for raw in text.splitlines():
        if not in_sources and SOURCES_HEADER_RE.match(raw):
            in_sources = True
            continue
        (src_lines if in_sources else body_lines).append(raw)
    body = "\n".join(body_lines).strip() or text.strip()
    return body, parse_sources(src_lines)

def main():
    # Call your CLI with --q (your parser requires it)
    rc, out = run(f"python rag.py ask --store {shlex.quote(STORE)} --q {shlex.quote(QUESTION)}")
    pathlib.Path("answer.txt").write_text(out, encoding="utf-8")

    answer, sources = split_answer_and_sources(out)

    payload = {
        "question": QUESTION,
        "answer": answer,
        "sources": sources
    }
    pathlib.Path("answers.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if not answer:
        print("ERROR: Empty answer produced by rag.py ask", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
