#!/usr/bin/env python3
import json, os, re, subprocess, sys, time, shlex, pathlib

QUESTION = os.environ.get("QUESTION", "What does the documentation say?")
STORE = os.environ.get("STORE", "store")

def run(cmd):
  p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
  # merge both streams so we never lose the model’s text if it prints to stderr
  out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
  return p.returncode, out.strip()

SRC_LINE = re.compile(r"^\[(\d+)\]\s+(.*?)(?:\s+\(score\s+([0-9.]+)\))?\s*$", re.I)

def parse_sources(lines):
  out = []
  for line in lines:
    m = SRC_LINE.match(line.strip())
    if m:
      rank = int(m.group(1))
      src = m.group(2)
      score = float(m.group(3)) if m.group(3) else None
      out.append({"rank": rank, "source": src, "score": score})
  return sorted(out, key=lambda x: x["rank"])

def split_answer_and_sources(text):
  # Split on a line that starts with “Sources” (any case, optional colon)
  body_lines, src_lines, in_sources = [], [], False
  for raw in text.splitlines():
    line = raw.rstrip("\r")
    if not in_sources and re.match(r"^\s*sources\s*:?\s*$", line, re.I):
      in_sources = True
      continue
    (src_lines if in_sources else body_lines).append(line)
  body = "\n".join(body_lines).strip()
  if not body:
    # Fallback: give the whole text so the page never shows empty
    body = text.strip()
  return body, parse_sources(src_lines)

def main():
  rc, out = run(f"python rag.py ask --store {shlex.quote(STORE)} --question {shlex.quote(QUESTION)}")
  # Always write a raw capture for debugging
  pathlib.Path("answer.txt").write_text(out, encoding="utf-8")

  answer, sources = split_answer_and_sources(out)
  payload = {
    "question": QUESTION,
    "result": {"answer": answer, "sources": sources},
    "updated_at": int(time.time())
  }
  pathlib.Path("answers.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

  # Hard-fail if empty so CI shows it
  if not answer:
    print("ERROR: Empty answer produced by rag.py ask", file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
  main()
