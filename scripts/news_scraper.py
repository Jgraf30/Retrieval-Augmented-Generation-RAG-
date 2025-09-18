#!/usr/bin/env python3
import os, re, json, time, hashlib, argparse, datetime, pathlib, textwrap
from typing import List, Dict, Optional
import requests
import feedparser

# Optional text extraction if we fall back to HTML pages (non-PDF)
# We keep it light — trafilatura works well for academic pages/abstracts
try:
    import trafilatura
except Exception:
    trafilatura = None

# -------------------------
# Config
# -------------------------
DEFAULT_OUTDIR = "data/news"
MAX_PER_RUN = int(os.getenv("NEWS_MAX_PER_RUN", "10"))
REQUEST_TIMEOUT = 30
SLEEP_BETWEEN = 0.6  # polite delay between requests

# arXiv Atom search queries — focused around RAG / dense retrieval / ColBERT / FiD, etc.
ARXIV_QUERIES = [
    # RAG terms
    "all:retrieval+augmented+generation",
    "all:retrieval-augmented+generation",
    "all:self-rag",
    "all:REPLUG",
    # dense retrieval foundations
    "all:dense+passage+retrieval",
    "all:ColBERT",
    "all:FiD",
    "all:REALM",
    "all:RETRO",
    "all:HyDE",
]
# fetch the newest items first
ARXIV_ENDPOINT = "http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=25&sortBy=submittedDate&sortOrder=descending"

# ACL Anthology recent (RSS) — broader NLP, we’ll pick titles/abstracts that hit our keywords
ACL_RSS = "https://aclanthology.org/feeds/papers.rss"

KEYWORDS = [
    "retrieval-augmented generation", "retrieval augmented generation", "rag",
    "dense passage retrieval", "dpr", "colbert", "fid", "realm", "retro", "hyde",
    "retrieval augmented", "retrieval-enhanced", "retrieval enhanced",
]

# -------------------------
# Helpers
# -------------------------
def slugify(s: str, maxlen: int = 80) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("_")
    return s or hashlib.md5(s.encode()).hexdigest()[:10]

def ensure_dir(p: str):
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path: str, obj):
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def good_keyword_hit(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)

def pick_pdf_link(links) -> Optional[str]:
    if not links:
        return None
    for ln in links:
        # arXiv pdf links often have rel='related' and type application/pdf
        if ("pdf" in (ln.get("title") or "").lower()) or ("pdf" in (ln.get("href") or "")) or (ln.get("type") == "application/pdf"):
            return ln.get("href")
    return None

def fetch_url(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "rag-news-scraper/1.0"})
        if resp.status_code == 200:
            return resp.content
        print(f"[WARN] GET {url} -> {resp.status_code}")
    except Exception as e:
        print(f"[WARN] GET {url} failed: {e}")
    return None

def extract_text_from_html(content: bytes) -> str:
    if trafilatura:
        try:
            downloaded = trafilatura.extract(content, include_comments=False, include_formatting=False)  # type: ignore
            if downloaded:
                return downloaded
        except Exception as e:
            print(f"[WARN] trafilatura extract failed: {e}")
    # fallback: naive strip
    try:
        txt = content.decode("utf-8", errors="ignore")
        txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.I)
        txt = re.sub(r"</p>", "\n\n", txt, flags=re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        txt = re.sub(r"[ \t]+", " ", txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        return txt.strip()
    except Exception:
        return ""

# -------------------------
# Sources
# -------------------------
def fetch_arxiv_items() -> List[Dict]:
    out: List[Dict] = []
    for q in ARXIV_QUERIES:
        url = ARXIV_ENDPOINT.format(query=q)
        print(f"[SRC] arXiv: {url}")
        feed = feedparser.parse(url)
        for e in feed.entries:
            title = e.get("title", "")
            summary = e.get("summary", "")
            if not (good_keyword_hit(title) or good_keyword_hit(summary)):
                continue
            pdf_url = pick_pdf_link(e.get("links"))
            page_url = e.get("link")  # abstract page
            pubdate = e.get("updated") or e.get("published") or ""
            out.append({
                "source": "arxiv",
                "title": title.strip(),
                "summary": summary.strip(),
                "page_url": page_url,
                "pdf_url": pdf_url,
                "date": pubdate,
                "id": e.get("id", page_url),
            })
        time.sleep(SLEEP_BETWEEN)
    return out

def fetch_acl_items() -> List[Dict]:
    print(f"[SRC] ACL: {ACL_RSS}")
    out: List[Dict] = []
    feed = feedparser.parse(ACL_RSS)
    for e in feed.entries:
        title = e.get("title", "")
        summary = e.get("summary", "")
        if not (good_keyword_hit(title) or good_keyword_hit(summary)):
            continue
        page_url = e.get("link")
        pubdate = e.get("updated") or e.get("published") or ""
        out.append({
            "source": "acl",
            "title": title.strip(),
            "summary": summary.strip(),
            "page_url": page_url,
            "pdf_url": None,  # ACL RSS doesn’t include PDF directly
            "date": pubdate,
            "id": page_url,
        })
    return out

# -------------------------
# Main scrape+save
# -------------------------
def main():
    ap = argparse.ArgumentParser(description="Weekly RAG news scraper (10 new items)")
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--limit", type=int, default=MAX_PER_RUN)
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    day_dir = os.path.join(args.outdir, today)
    ensure_dir(day_dir)

    seen_path = os.path.join(args.outdir, "_seen_urls.json")
    seen = set(load_json(seen_path, default=[]))

    # Gather candidates
    items = []
    items.extend(fetch_arxiv_items())
    items.extend(fetch_acl_items())

    # Sort newest first (arXiv “updated” is ISO8601-ish, but for safety just reverse collected order)
    # We’ll keep relative order: arXiv queries newest first already; ACL feed is newest first.
    # Dedupe by page_url/pdf_url/id
    deduped: List[Dict] = []
    seen_ids = set()
    for it in items:
        uid = it.get("id") or it.get("page_url") or it.get("pdf_url")
        if not uid or uid in seen_ids:
            continue
        seen_ids.add(uid)
        deduped.append(it)

    # Filter out those we've already saved in previous runs
    new_items = []
    for it in deduped:
        key = it.get("pdf_url") or it.get("page_url") or it.get("id")
        if key in seen:
            continue
        new_items.append(it)
        if len(new_items) >= args.limit:
            break

    if not new_items:
        print("[INFO] No new items found this run.")
        return 0

    manifest_path = os.path.join(args.outdir, "manifest.json")
    manifest = load_json(manifest_path, default={"generated_at": "", "batches": []})

    saved_entries = []
    for it in new_items:
        title = it["title"]
        page_url = it.get("page_url")
        pdf_url = it.get("pdf_url")
        base = slugify(title) or hashlib.md5((page_url or pdf_url or title).encode()).hexdigest()[:12]
        meta = {
            "title": title,
            "source": it["source"],
            "date": it.get("date"),
            "page_url": page_url,
            "pdf_url": pdf_url,
            "saved_at": today,
            "files": {},
        }

        if pdf_url:
            # download PDF
            pdf_bytes = fetch_url(pdf_url)
            if pdf_bytes and pdf_bytes.startswith(b"%PDF"):
                pdf_path = os.path.join(day_dir, f"{base}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)
                meta["files"]["pdf"] = os.path.relpath(pdf_path)
                print(f"[SAVE] PDF -> {pdf_path}")
            else:
                print(f"[WARN] PDF fetch failed or not a PDF: {pdf_url}")

        if not meta["files"]:
            # fallback: fetch abstract/page HTML and store as .txt
            if page_url:
                html = fetch_url(page_url)
                if html:
                    text = extract_text_from_html(html)
                    if text:
                        txt_path = os.path.join(day_dir, f"{base}.txt")
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(textwrap.dedent(text).strip())
                        meta["files"]["txt"] = os.path.relpath(txt_path)
                        print(f"[SAVE] TXT -> {txt_path}")
                    else:
                        print(f"[WARN] Could not extract text from {page_url}")

        # only mark seen if we saved something useful
        if meta["files"]:
            saved_entries.append(meta)
            seen_key = it.get("pdf_url") or it.get("page_url") or it.get("id")
            if seen_key:
                seen.add(seen_key)

        time.sleep(SLEEP_BETWEEN)

    if not saved_entries:
        print("[INFO] Found new candidates, but none saved successfully.")
        return 0

    # Update manifest
    batch = {
        "date": today,
        "count": len(saved_entries),
        "items": saved_entries
    }
    manifest["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    manifest["batches"].append(batch)
    save_json(manifest_path, manifest)
    save_json(seen_path, sorted(list(seen)))

    print(f"[DONE] Saved {len(saved_entries)} new article(s) to {day_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
