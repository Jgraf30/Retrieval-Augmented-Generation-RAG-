#!/usr/bin/env bash
set -euo pipefail

# -------------------------------
# RAG dataset fetcher (20 docs)
# - Research: direct PDFs from arXiv/ACL
# - Guides: official docs (HTML scraped to .txt)
# - No vendor blogs
# -------------------------------

ROOT="$(pwd)"
DATA_DIR="${ROOT}/data"
mkdir -p "${DATA_DIR}"

have() { command -v "$1" >/dev/null 2>&1; }

# Crude HTML -> text scrubber (prefer lynx/w3m if available)
html_to_txt() {
  # $1: input html; $2: output txt
  if have lynx; then
    lynx -dump -nolist "$1" > "$2"
  elif have w3m; then
    w3m -dump "$1" > "$2"
  else
    # Fallback: remove tags; keep newlines roughly
    sed -E 's/<[[:space:]]*br[[:space:]]*\/?>/\n/Ig; s/<\/p>/\n\n/Ig; s/<[^>]+>//g' "$1" \
      | sed -E 's/[[:space:]]+/ /g; s/ *\n+/\n/g' > "$2"
  fi
}

get_pdf() {
  local url="$1" out="$2"
  echo "→ PDF: $out"
  curl -L --fail --retry 3 --retry-delay 2 "$url" -o "$out"
}

get_doc_as_txt() {
  local url="$1" out="$2" tmp
  tmp="$(mktemp)"
  echo "→ DOC: $out (HTML→TXT)"
  curl -L --fail --retry 3 --retry-delay 2 "$url" -o "$tmp"
  html_to_txt "$tmp" "$out"
  rm -f "$tmp"
}

echo "== Downloading research PDFs =="

# 1) RAG (Lewis et al., 2020)
get_pdf "https://arxiv.org/pdf/2005.11401" \
  "${DATA_DIR}/rag_lewis_2020.pdf"

# 2) REALM (Guu et al., 2020)
get_pdf "https://arxiv.org/pdf/2002.08909" \
  "${DATA_DIR}/realm_guu_2020.pdf"

# 3) DPR (Karpukhin et al., 2020)
get_pdf "https://arxiv.org/pdf/2004.04906" \
  "${DATA_DIR}/dpr_karpukhin_2020.pdf"

# 4) ColBERT (Khattab & Zaharia, 2020)
get_pdf "https://arxiv.org/pdf/2004.12832" \
  "${DATA_DIR}/colbert_khattab_2020.pdf"

# 5) FiD (Izacard & Grave, 2020/21)
get_pdf "https://arxiv.org/pdf/2007.01282" \
  "${DATA_DIR}/fid_izacard_grave_2020.pdf"

# 6) RETRO (DeepMind, 2021)
get_pdf "https://arxiv.org/pdf/2112.04426" \
  "${DATA_DIR}/retro_borgeaud_2021.pdf"

# 7) HyDE (Gao et al., 2022)
get_pdf "https://arxiv.org/pdf/2212.10496" \
  "${DATA_DIR}/hyde_gao_2022.pdf"

# 8) REPLUG (Shi et al., 2023) – arXiv version
get_pdf "https://arxiv.org/pdf/2301.12652" \
  "${DATA_DIR}/replug_shi_2023.pdf"

# 9) Self-RAG (Asai et al., 2023)
get_pdf "https://arxiv.org/pdf/2310.11511" \
  "${DATA_DIR}/selfrag_asai_2023.pdf"

# 10) Survey: Retrieval-Augmented Text Generation (Huang & Huang, 2024)
get_pdf "https://arxiv.org/pdf/2312.10997" \
  "${DATA_DIR}/survey_rag_huang_2024.pdf"

# 11) Survey: Evaluation of RAG (Yu et al., 2024)
get_pdf "https://arxiv.org/pdf/2405.07437" \
  "${DATA_DIR}/survey_eval_rag_yu_2024.pdf"

# 12) Survey: Comprehensive RAG (Gupta et al., 2024)
get_pdf "https://arxiv.org/pdf/2410.12837" \
  "${DATA_DIR}/survey_comprehensive_rag_gupta_2024.pdf"


echo "== Downloading official guides as TXT =="

# 13) LangChain (Python) – RAG Tutorial (official docs)
get_doc_as_txt "https://python.langchain.com/docs/tutorials/rag/" \
  "${DATA_DIR}/langchain_rag_tutorial_python.txt"

# 14) LangChain (Part 2 – QA chat history)
get_doc_as_txt "https://python.langchain.com/docs/tutorials/qa_chat_history/" \
  "${DATA_DIR}/langchain_rag_part2_chat_history.txt"

# 15) Haystack – Get Started (build first RAG)
get_doc_as_txt "https://docs.haystack.deepset.ai/docs/get_started" \
  "${DATA_DIR}/haystack_get_started_rag.txt"

# 16) Haystack – First RAG pipeline tutorial
get_doc_as_txt "https://haystack.deepset.ai/tutorials/27_first_rag_pipeline" \
  "${DATA_DIR}/haystack_first_rag_pipeline.txt"

# 17) LlamaIndex – Introduction to RAG (official docs)
get_doc_as_txt "https://docs.llamaindex.ai/en/stable/understanding/rag/" \
  "${DATA_DIR}/llamaindex_intro_rag.txt"

# 18) LlamaIndex – Tutorials/Cookbooks index (official)
get_doc_as_txt "https://docs.llamaindex.ai/en/stable/examples/cookbooks/oreilly_course_cookbooks/" \
  "${DATA_DIR}/llamaindex_cookbooks_overview.txt"

# 19) OpenAI Cookbook – RAG with Elasticsearch
get_doc_as_txt "https://cookbook.openai.com/examples/vector_databases/elasticsearch/elasticsearch-retrieval-augmented-generation" \
  "${DATA_DIR}/openai_cookbook_rag_elasticsearch.txt"

# 20) OpenAI Cookbook – Evaluate RAG with LlamaIndex
get_doc_as_txt "https://cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex" \
  "${DATA_DIR}/openai_cookbook_evaluate_rag_llamaindex.txt"


echo
echo "== Done =="
ls -lh "${DATA_DIR}"
