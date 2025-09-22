#!/usr/bin/env python3
import json, os, pathlib, re, sys

OUT = pathlib.Path("questions.json")
DATA = pathlib.Path("questions.json")

def default_questions_from_docs():
  # Scan /data for doc names and generate a small question set
  data_dir = pathlib.Path("data")
  docs = []
  for p in data_dir.rglob("*"):
    if p.suffix.lower() in {".pdf",".txt",".md",".html",".htm"}:
      docs.append(p)
  # base questions
  q = [
    "What does the documentation say?",
    "Summarize the key points.",
    "What are the main findings?",
    "List the top 5 takeaways.",
    "What recommendations are provided?"
  ]
  # Add a couple doc-specific questions (max 5 to keep it short)
  for p in docs[:5]:
    name = p.name
    q.append(f"What is {name} about?")
    q.append(f"Give a concise summary of {name}.")
  # Deduplicate while preserving order
  seen=set(); out=[]
  for s in q:
    if s not in seen:
      seen.add(s); out.append(s)
  return out[:12]  # cap length to keep runs fast

def main():
  # If a questions.json already exists (user-provided), keep it
  if pathlib.Path("questions.json").exists():
    try:
      existing = json.loads(pathlib.Path("questions.json").read_text(encoding="utf-8"))
      if isinstance(existing, list) and existing:
        print("Using existing questions.json")
        return
    except Exception:
      pass
  questions = default_questions_from_docs()
  OUT.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"Wrote {OUT} with {len(questions)} question(s).")

if __name__ == "__main__":
  main()
