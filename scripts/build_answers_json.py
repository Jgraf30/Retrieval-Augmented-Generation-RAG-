#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, shlex, pathlib

QUESTION = os.environ.get("QUESTION", "What does the documentation say?")
STORE = os.environ.get("STORE", "store")

# Accept source lines like:
# [1] path/file.pdf (score 0.777) [begin 0 end 6702]
SRC_RE = re.compile(
    r"^\s*\[(?P<rank>\d+)\]\s+(?P<source>.+?)(?:\s+\(score\s+(?P<score>[0-9.]+)\))?(?:\s+\[(?:begin\s+(?P<begin>\d+))?(?:\s+end\s+(?P<end>\d+))?\])?\s*$",
    re.I
)

def run(cmd: str):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    return p.returncode, out.strip()

def try_parse_json_payload(text: str):
    """If rag.py prints JSON, normalize to flat schema."""
    t = text.strip()
    if not t.startswith("{"):
        return None
    try:
        obj = json.loads(t)
    except Exception:
        return None
    # Try common shapes
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
    # Normalize sources to expected keys
    norm_sources = []
    if isinstance(sources, list):
        for i, s in enumerate(sources, 1):
            if isinstance(s, dict):
                norm_sources.append({
                    "rank": s.get("rank", i),
                    "score": s.get("score"),
                    "source": s.get("source") or s.get("path") or s.get("id") or "(unknown)",
                    "begin": s.get("begin"),
                    "end": s.get("end"),
                })
            else:
                norm_sources.append({"rank": i, "source": str(s), "score": None, "begin": None, "end": None})
    return {
        "question": obj.get("question") or QUESTION,
        "answer": str(answer or "").strip(),
        "sources": norm_sources
    }

def parse_sources_from_lines(lines):
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
    # If there's an explicit "Sources" header, split there; otherwise strip trailing source-like lines.
    lines = text.splitlines()
    # 1) Look for a "Sources" header line
    body_lines, src_lines, in_sources = [], [], False
    for raw in lines:
        if not in_sources and re.match(r"^\s*sources\s*:?\s*$", raw, re.I):
            in_sources = True
            continue
        (src_lines if in_sources else body_lines).append(raw)
    if in_sources:
        body = "\n".join(body_lines).strip()
        sources = parse_sources_from_lines(src_lines)
        return body, sources
    # 2) No header: peel off source-like lines from the bottom
    rev = list(reversed(lines))
    tail = []
    for raw in rev:
        if SRC_RE.match(raw.strip()):
            tail.append(raw)
        else:
            break
    if tail:
        keep_count = len(lines) - len(tail)
        body = "\n".join(lines[:keep_count]).strip()
        sources = parse_sources_from_lines(reversed(tail))
        return body, sources
    # 3) Just body
    return text.strip(), []

def main():
    rc, out = run(f"python rag.py ask --store {shlex.quote(STORE)} --q {shlex.quote(QUESTION)}")
    pathlib.Path("answer.txt").write_text(out, encoding="utf-8")

    # First, if JSON was emitted, use it.
    payload = try_parse_json_payload(out)
    if not payload:
        # Fallback: parse plain text + source lines
        body, sources = split_text_and_sources(out)
        payload = {
            "question": QUESTION,
            "answer": body,
            "sources": sources
        }

    # Final guard: never write an empty answer silently
    if not payload.get("answer"):
        payload["answer"] = "(no model output)"

    pathlib.Path("answers.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # If the CLI failed AND we only have the placeholder, fail the job so you see it in logs
    if rc != 0 and payload.get("answer") == "(no model output)":
        print("ERROR: rag.py ask failed and produced no usable output", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
