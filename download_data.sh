#!/usr/bin/env bash
# RAG dataset fetcher (20 docs)
# - 12 arXiv PDFs + 8 official guides saved as .txt
# - Multiple fallbacks per item
# - NEVER fails the job on 404 (or any curl error)
# - Writes logs: download_ok.log, download_errors.log
# - Always exits 0

set +e  # disable 'exit on error' no matter what the runner default is
set -u
set -o pipefail

ROOT="$(pwd)"
DATA_DIR="${ROOT}/data"
LOG_OK="${ROOT}/download_ok.log"
LOG_ERR="${ROOT}/download_errors.log"

mkdir -p "${DATA_DIR}"
: > "${LOG_OK}"
: > "${LOG_ERR}"

# --- helpers ---------------------------------------------------------------

have() { command -v "$1" >/dev/null 2>&1; }

# Return 0 but indicate success/failure via status text + logs.
# We DO NOT use --fail so curl never sets exit code for 404.
# Instead, capture HTTP status and decide ourselves.
_fetch_one() {
  local url="$1" out="$2"
  echo "   trying: $url"
  # -S to show errors on stderr, -L follow redirects, -s silent progress
  http_code=$(curl -sSL -w "%{http_code}" -o "$out" "$url" || echo "000")
  if [[ "$http_code" =~ ^2|3[0-9]{2}$ ]]; then
    echo "OK  $out  <=  $url (HTTP $http_code)" >> "${LOG_OK}"
    return 0
  else
    echo "MISS $out  <=  $url (HTTP $http_code)" >> "${LOG_ERR}"
    rm -f "$out" 2>/dev/null || true
    return 1
  fi
}

# Try multiple URLs; never return non-zero
try_fetch() {
  local out="$1"; shift
  local ok=1
  for url in "$@"; do
    if _fetch_one "$url" "$out"; then
      ok=0
      break
    fi
  done
  # Always return 0 so the job never fails here
  return 0
}

# Minimal HTML→TXT (no external deps)
html_to_txt() {
  local in="$1" out="$2"
  sed -E 's/<[[:space:]]*br[[:space:]]*\/?>/\n/Ig; s/<\/p>/\n\n/Ig; s/<[^>]+>//g' "$in" \
    | sed -E 's/[ \t]+/ /g; s/ *\n+/\n/g; s/\n{3,}/\n\n/g' > "$out"
}

get_pdf() {
  local out="$1"; shift
  echo "→ PDF: $out"
  try_fetch "$out" "$@"
}

get_doc_as_txt() {
  local out="$1"; shift
  local tmp
  tmp="$(mktemp)"
  echo "→ DOC: $out (HTML→TXT)"
  try_fetch "$tmp" "$@"
  if [[ -s "$tmp" ]]; then
    html_to_txt "$tmp" "$out" || { echo "WARN: HTML->TXT failed for $out" | tee -a "${LOG_ERR}"; rm -f "$out"; }
  else
    echo "MISS $out  (no HTML fetched)" >> "${LOG_ERR}"
  fi
  rm -f "$tmp" 2>/dev/null || true
}

# --- downloads -------------------------------------------------------------

echo "== Downloading research PDFs (12) =="

# 1) RAG (Lewis et al., 2020)
get_pdf "${DATA_DIR}/rag_lewis_2020.pdf" \
  "https://arxiv.org/pdf/2005.11401.pdf" \
  "https://arxiv.org/pdf/2005.11401"

# 2) REALM (Guu et al., 2020)
get_pdf "${DATA_DIR}/realm_guu_2020.pdf" \
  "https://arxiv.org/pdf/2002.08909.pdf" \
  "https://arxiv.org/pdf/2002.08909"

# 3) DPR (Karpukhin et al., 2020)
get_pdf "${DATA_DIR}/dpr_karpukhin_2020.pdf" \
  "https://arxiv.org/pdf/2004.04906.pdf" \
  "https://arxiv.org/pdf/2004.04906"

# 4) ColBERT (Khattab & Zaharia, 2020)
get_pdf "${DATA_DIR}/colbert_khattab_2020.pdf" \
  "https://arxiv.org/pdf/2004.12832.pdf" \
  "https://arxiv.org/pdf/2004.12832"

# 5) FiD (Izacard & Grave, 2020/21)
get_pdf "${DATA_DIR}/fid_izacard_grave_2020.pdf" \
  "https://arxiv.org/pdf/2007.01282.pdf" \
  "https://arxiv.org/pdf/2007.01282"

# 6) RETRO (Borgeaud et al., 2021)
get_pdf "${DATA_DIR}/retro_borgeaud_2021.pdf" \
  "https://arxiv.org/pdf/2112.04426.pdf" \
  "https://arxiv.org/pdf/2112.04426"

# 7) HyDE (Gao et al., 2022)
get_pdf "${DATA_DIR}/hyde_gao_2022.pdf" \
  "https://arxiv.org/pdf/2212.10496.pdf" \
  "https://arxiv.org/pdf/2212.10496"

# 8) REPLUG (Shi et al., 2023)
get_pdf "${DATA_DIR}/replug_shi_2023.pdf" \
  "https://arxiv.org/pdf/2301.12652.pdf" \
  "https://arxiv.org/pdf/2301.12652"

# 9) Self-RAG (Asai et al., 2023)
get_pdf "${DATA_DIR}/selfrag_asai_2023.pdf" \
  "https://arxiv.org/pdf/2310.11511.pdf" \
  "https://arxiv.org/pdf/2310.11511"

# 10) Survey: Retrieval-Augmented Text Generation (Huang et al., 2024)
get_pdf "${DATA_DIR}/survey_rag_huang_2024.pdf" \
  "https://arxiv.org/pdf/2312.10997.pdf" \
  "https://arxiv.org/pdf/2312.10997"

# 11) Survey: Evaluation of RAG (Yu et al., 2024)
get_pdf "${DATA_DIR}/survey_eval_rag_yu_2024.pdf" \
  "https://arxiv.org/pdf/2405.07437.pdf" \
  "https://arxiv.org/pdf/2405.07437"

# 12) Survey: Comprehensive RAG (Gupta et al., 2024) — id may change, include abs fallback
get_pdf "${DATA_DIR}/survey_comprehensive_rag_gupta_2024.pdf" \
  "https://arxiv.org/pdf/2410.12837.pdf" \
  "https://arxiv.org/pdf/2410.12837" \
  "https://arxiv.org/abs/2410.12837"

echo "== Downloading official guides/tutorials as TXT (8) =="

# 13) LangChain (Python) – RAG Tutorial
get_doc_as_txt "${DATA_DIR}/langchain_rag_tutorial_python.txt" \
  "https://python.langchain.com/docs/tutorials/rag/" \
  "https://python.langchain.com/docs/tutorials/rag" \
  "https://web.archive.org/web/*/https://python.langchain.com/docs/tutorials/rag/"

# 14) LangChain – QA chat history
get_doc_as_txt "${DATA_DIR}/langchain_rag_part2_chat_history.txt" \
  "https://python.langchain.com/docs/tutorials/qa_chat_history/" \
  "https://python.langchain.com/docs/tutorials/qa_chat_history" \
  "https://web.archive.org/web/*/https://python.langchain.com/docs/tutorials/qa_chat_history/"

# 15) Haystack – Get Started
get_doc_as_txt "${DATA_DIR}/haystack_get_started_rag.txt" \
  "https://docs.haystack.deepset.ai/docs/get_started" \
  "https://web.archive.org/web/*/https://docs.haystack.deepset.ai/docs/get_started"

# 16) Haystack – First RAG pipeline tutorial
get_doc_as_txt "${DATA_DIR}/haystack_first_rag_pipeline.txt" \
  "https://haystack.deepset.ai/tutorials/27_first_rag_pipeline" \
  "https://web.archive.org/web/*/https://haystack.deepset.ai/tutorials/27_first_rag_pipeline"

# 17) LlamaIndex – Introduction to RAG
get_doc_as_txt "${DATA_DIR}/llamaindex_intro_rag.txt" \
  "https://docs.llamaindex.ai/en/stable/understanding/rag/" \
  "https://docs.llamaindex.ai/en/latest/understanding/rag/" \
  "https://web.archive.org/web/*/https://docs.llamaindex.ai/en/stable/understanding/rag/"

# 18) LlamaIndex – O’Reilly course cookbooks overview
get_doc_as_txt "${DATA_DIR}/llamaindex_cookbooks_overview.txt" \
  "https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/" \
  "https://docs.llamaindex.ai/en/latest/examples/cookbooks/oreilly_course_cookbooks/" \
  "https://web.archive.org/web/*/https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/"

# 19) OpenAI Cookbook – RAG with Elasticsearch (multiple slugs + archive)
get_doc_as_txt "${DATA_DIR}/openai_cookbook_rag_elasticsearch.txt" \
  "https://cookbook.openai.com/examples/vector_databases/elasticsearch/elasticsearch-retrieval-augmented-generation" \
  "https://cookbook.openai.com/examples/retrieval_augmented_generation_with_elasticsearch" \
  "https://cookbook.openai.com/examples/retrieval_augmented_generation" \
  "https://web.archive.org/web/*/https://cookbook.openai.com/examples/retrieval_augmented_generation"

# 20) OpenAI Cookbook – Evaluate RAG with LlamaIndex (multiple slugs + archive)
get_doc_as_txt "${DATA_DIR}/openai_cookbook_evaluate_rag_llamaindex.txt" \
  "https://cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex" \
  "https://cookbook.openai.com/examples/evaluate_rag_with_llamaindex" \
  "https://web.archive.org/web/*/https://cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex"

echo
echo "== SUMMARY =="
echo "Downloaded OK (count): $(wc -l < "${LOG_OK}" 2>/dev/null || echo 0)"
tail -n +1 "${LOG_OK}" 2>/dev/null || true
echo
echo "Misses (count): $(wc -l < "${LOG_ERR}" 2>/dev/null || echo 0)"
tail -n +1 "${LOG_ERR}" 2>/dev/null || true
echo
echo "Files in data/:"
ls -lh "${DATA_DIR}" || true

exit 0
