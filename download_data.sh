#!/usr/bin/env bash
# RAG dataset fetcher (12 research PDFs + 8 official guides as TXT)
# - Resilient to 404s (will skip missing docs instead of failing the job)
# - Uses fallback URLs where available
set -uo pipefail

ROOT="$(pwd)"
DATA_DIR="${ROOT}/data"
mkdir -p "${DATA_DIR}"

have() { command -v "$1" >/dev/null 2>&1; }

# Simple HTML -> TXT scrubber (lynx/w3m if present; otherwise sed fallback)
html_to_txt() {
  in="$1"; out="$2"
  if have lynx; then
    lynx -dump -nolist "$in" > "$out"
  elif have w3m; then
    w3m -dump "$in" > "$out"
  else
    sed -E 's/<[[:space:]]*br[[:space:]]*\/?>/\n/Ig; s/<\/p>/\n\n/Ig; s/<[^>]+>//g' "$in" \
      | sed -E 's/[[:space:]]+/ /g; s/ *\n+/\n/g' > "$out"
  fi
}

# Try a list of candidate URLs, return 0 when one succeeds
try_curl() {
  out="$1"; shift
  for url in "$@"; do
    echo "   trying $url"
    if curl -L --fail --retry 3 --retry-delay 2 "$url" -o "$out"; then
      return 0
    fi
  done
  return 1
}

get_pdf() {
  out="$1"; shift
  echo "→ PDF: $out"
  if ! try_curl "$out" "$@"; then
    echo "[WARN] Could not fetch PDF for $out — skipping."
    rm -f "$out"
  fi
}

get_doc_as_txt() {
  out="$1"; shift
  tmp="$(mktemp)"
  echo "→ DOC: $out (HTML→TXT)"
  if ! try_curl "$tmp" "$@"; then
    echo "[WARN] Could not fetch HTML for $out — skipping."
    rm -f "$tmp"
    return 0
  fi
  html_to_txt "$tmp" "$out" || echo "[WARN] HTML→TXT failed for $out"
  rm -f "$tmp"
}

echo "== Downloading research PDFs (12) =="

# 1) RAG (Lewis et al., 2020)
get_pdf "${DATA_DIR}/rag_lewis_2020.pdf" \
  "https://arxiv.org/pdf/2005.11401"

# 2) REALM (Guu et al., 2020)
get_pdf "${DATA_DIR}/realm_guu_2020.pdf" \
  "https://arxiv.org/pdf/2002.08909"

# 3) DPR (Karpukhin et al., 2020)
get_pdf "${DATA_DIR}/dpr_karpukhin_2020.pdf" \
  "https://arxiv.org/pdf/2004.04906"

# 4) ColBERT (Khattab & Zaharia, 2020)
get_pdf "${DATA_DIR}/colbert_khattab_2020.pdf" \
  "https://arxiv.org/pdf/2004.12832"

# 5) FiD (Izacard & Grave, 2020/21)
get_pdf "${DATA_DIR}/fid_izacard_grave_2020.pdf" \
  "https://arxiv.org/pdf/2007.01282"

# 6) RETRO (Borgeaud et al., 2021)
get_pdf "${DATA_DIR}/retro_borgeaud_2021.pdf" \
  "https://arxiv.org/pdf/2112.04426"

# 7) HyDE (Gao et al., 2022)
get_pdf "${DATA_DIR}/hyde_gao_2022.pdf" \
  "https://arxiv.org/pdf/2212.10496"

# 8) REPLUG (Shi et al., 2023)
get_pdf "${DATA_DIR}/replug_shi_2023.pdf" \
  "https://arxiv.org/pdf/2301.12652"

# 9) Self-RAG (Asai et al., 2023/ICLR 2024)
get_pdf "${DATA_DIR}/selfrag_asai_2023.pdf" \
  "https://arxiv.org/pdf/2310.11511"

# 10) Survey: Retrieval-Augmented Text Generation (Huang et al., 2024)
get_pdf "${DATA_DIR}/survey_rag_huang_2024.pdf" \
  "https://arxiv.org/pdf/2312.10997"

# 11) Survey: Evaluation of RAG (Yu et al., 2024)
get_pdf "${DATA_DIR}/survey_eval_rag_yu_2024.pdf" \
  "https://arxiv.org/pdf/2405.07437"

# 12) Survey: Comprehensive RAG (Gupta et al., 2024) — if arXiv id changes, this will be skipped
get_pdf "${DATA_DIR}/survey_comprehensive_rag_gupta_2024.pdf" \
  "https://arxiv.org/pdf/2410.12837"

echo "== Downloading official guides/tutorials as TXT (8) =="

# 13) LangChain (Python) – RAG Tutorial
get_doc_as_txt "${DATA_DIR}/langchain_rag_tutorial_python.txt" \
  "https://python.langchain.com/docs/tutorials/rag/"

# 14) LangChain – QA chat history (conversational RAG)
get_doc_as_txt "${DATA_DIR}/langchain_rag_part2_chat_history.txt" \
  "https://python.langchain.com/docs/tutorials/qa_chat_history/"

# 15) Haystack – Get Started
get_doc_as_txt "${DATA_DIR}/haystack_get_started_rag.txt" \
  "https://docs.haystack.deepset.ai/docs/get_started"

# 16) Haystack – First RAG pipeline tutorial
get_doc_as_txt "${DATA_DIR}/haystack_first_rag_pipeline.txt" \
  "https://haystack.deepset.ai/tutorials/27_first_rag_pipeline"

# 17) LlamaIndex – Introduction to RAG
get_doc_as_txt "${DATA_DIR}/llamaindex_intro_rag.txt" \
  "https://docs.llamaindex.ai/en/stable/understanding/rag/" \
  "https://docs.llamaindex.ai/en/latest/understanding/rag/"

# 18) LlamaIndex – O’Reilly course cookbooks overview
get_doc_as_txt "${DATA_DIR}/llamaindex_cookbooks_overview.txt" \
  "https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/" \
  "https://docs.llamaindex.ai/en/latest/examples/cookbooks/oreilly_course_cookbooks/"

# 19) OpenAI Cookbook – RAG with Elasticsearch (path sometimes moves; try multiple)
get_doc_as_txt "${DATA_DIR}/openai_cookbook_rag_elasticsearch.txt" \
  "https://cookbook.openai.com/examples/vector_databases/elasticsearch/elasticsearch-retrieval-augmented-generation" \
  "https://cookbook.openai.com/examples/retrieval_augmented_generation_with_elasticsearch" \
  "https://cookbook.openai.com/examples/retrieval_augmented_generation"

# 20) OpenAI Cookbook – Evaluate RAG with LlamaIndex (alternate slugs)
get_doc_as_txt "${DATA_DIR}/openai_cookbook_evaluate_rag_llamaindex.txt" \
  "https://cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex" \
  "https://cookbook.openai.com/examples/evaluation_rag_with_llamaindex" \
  "https://cookbook.openai.com/examples/evaluate_rag_with_llamaindex"

echo
echo "== Download complete =="
ls -lh "${DATA_DIR}" || true
