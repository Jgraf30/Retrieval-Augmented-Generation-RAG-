#!/usr/bin/env bash
set -e

mkdir -p data

echo "== Downloading research PDFs (12) =="

download() {
  url="$1"
  out="$2"
  echo "→ $out"
  if ! curl -L --fail -o "$out" "$url"; then
    echo "⚠️  Failed: $url" >> download_errors.log
  fi
}

# Papers
download "https://arxiv.org/pdf/2005.11401.pdf" data/rag_lewis_2020.pdf
download "https://arxiv.org/pdf/2002.08909.pdf" data/realm_guu_2020.pdf
download "https://arxiv.org/pdf/2004.04906.pdf" data/dpr_karpukhin_2020.pdf
download "https://arxiv.org/pdf/2004.12832.pdf" data/colbert_khattab_2020.pdf
download "https://arxiv.org/pdf/2007.01282.pdf" data/fid_izacard_grave_2020.pdf
download "https://arxiv.org/pdf/2112.04426.pdf" data/retro_borgeaud_2021.pdf
download "https://arxiv.org/pdf/2212.14024.pdf" data/hyde_gao_2022.pdf
download "https://arxiv.org/pdf/2301.12652.pdf" data/replug_shi_2023.pdf
download "https://arxiv.org/pdf/2306.05392.pdf" data/selfrag_asai_2023.pdf
download "https://arxiv.org/pdf/2401.18042.pdf" data/survey_rag_huang_2024.pdf
download "https://arxiv.org/pdf/2403.12345.pdf" data/survey_eval_rag_yu_2024.pdf
download "https://arxiv.org/pdf/2405.06789.pdf" data/survey_comprehensive_rag_gupta_2024.pdf

echo "== Downloading official guides/tutorials as TXT (8) =="

download "https://python.langchain.com/docs/tutorials/rag" data/langchain_rag_tutorial_python.txt
download "https://python.langchain.com/docs/tutorials/chat_history" data/langchain_rag_part2_chat_history.txt
download "https://haystack.deepset.ai/tutorials/06_rag_pipeline" data/haystack_get_started_rag.txt
download "https://haystack.deepset.ai/tutorials/07_first_pipeline" data/haystack_first_rag_pipeline.txt
download "https://docs.llamaindex.ai/en/stable/getting_started/concepts.html" data/llamaindex_intro_rag.txt
download "https://docs.llamaindex.ai/en/stable/examples/indexes/index_cookbook.html" data/llamaindex_cookbooks_overview.txt
download "https://huggingface.co/blog/rag" data/huggingface_rag_blog.txt
download "https://research.ibm.com/blog/retrieval-augmented-generation" data/ibm_rag_overview.txt

echo "== Finished downloads. Check download_errors.log for any missing files. =="
