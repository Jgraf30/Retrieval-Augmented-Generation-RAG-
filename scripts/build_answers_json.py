#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, shlex, pathlib

QUESTION = os.environ.get("QUESTION", "What does the documentation say?")
STORE = os.environ.get("STORE", "store")

def run(cmd):
  p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
  out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
  return p.returncode, out.strip()

def parse_sources(lines):
  out = []
  for line in lines:
    m = re.match(r"\[(\d+)\]\s+(.*?)(?:\s+\(score\s+([0-9.]+)\))?\s*$", line.strip())
    if m:
      rank = int(m.group(1))
      src = m.group(2)
      score = float(m.group(3)) if m.group(3) else None
      out.append({"rank": rank, "source": src, "score": score})
  return sorted(out, key=lambda x: x["rank"])

def split_body_and_sources(text):
  body_lines = []
  src_lines = []
  in_sources = False
  for line in text.splitlines():
    if not in_sources and line.strip().lower().startswith("sources"):
      in_sources = True
      continue
    (src_lines if in_sources else body_lines).append(line)
  body = "\n".join(body_lines).strip()
  return (body if body else text.strip(), parse_sources(src_lines))

def main():
  # call your existing CLI
  rc, out = run(f"python rag.py ask --store {shlex.quote(STORE)} --question {shlex.quote(QUESTION)}")
  if rc != 0 and not out:
    print("RAG ask failed and produced no output", file=sys.stderr)
    sys.exit(1)

  answer, sources = split_body_and_sources(out)

  payload = {
    "question": QUESTION,
    "result": {
      "answer": answer,
      "sources": sources
    },
    "updated_at": int(time.time())
  }
  pathlib.Path("answers.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
  print("answers.json written")

if __name__ == "__main__":
  main()
