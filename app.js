async function loadAnswers() {
  try {
    const r = await fetch("answers.json", { cache: "no-store" });
    if (!r.ok) throw new Error("answers.json missing");
    const data = await r.json();

    // Question
    const qEl = document.getElementById("q");
    if (qEl) qEl.textContent = data.question || "(no question)";

    // Answer (preserve line breaks as <br/>)
    const aEl = document.getElementById("ans");
    if (aEl) {
      const ans = data?.result?.answer || "";
      aEl.innerHTML = ans ? ans.replace(/\n/g, "<br/>") : "(no answer)";
    }

    // Sources
    const list = document.getElementById("srcs");
    if (list) {
      list.innerHTML = "";
      (data.result?.sources || []).forEach(s => {
        const li = document.createElement("li");
        const score = (typeof s.score === "number")
          ? ` (score ${Number(s.score).toFixed(3)})`
          : "";
        li.textContent = `[${s.rank}] ${s.source}${score}`;
        list.appendChild(li);
      });
    }

    // Timestamp
    const stamp = document.getElementById("stamp");
    if (stamp && data.updated_at) {
      const dt = new Date(data.updated_at * 1000);
      stamp.textContent = `Updated ${dt.toLocaleString()}`;
    }
  } catch (e) {
    const aEl = document.getElementById("ans");
    if (aEl) aEl.textContent = "No RAG output available yet.";
  }
}

async function loadNews() {
  const container = document.getElementById("news");
  if (!container) return;
  try {
    const r = await fetch("data/news/manifest.json", { cache: "no-store" });
    if (!r.ok) {
      container.textContent = "No news manifest yet.";
      return;
    }
    const data = await r.json();
    const batches = (data.batches || []).slice(-3).reverse();
    if (batches.length === 0) {
      container.textContent = "No recent articles yet.";
      return;
    }
    container.innerHTML = "";
    batches.forEach(b => {
      const sec = document.createElement("div");
      sec.className = "news-batch";
      const h = document.createElement("h3");
      h.textContent = `Batch ${b.date} — ${b.count} item(s)`;
      sec.appendChild(h);
      const ul = document.createElement("ul");
      (b.items || []).forEach(it => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.textContent = it.title || "(untitled)";
        const href = it.files?.pdf
          ? it.files.pdf
          : (it.files?.txt ? it.files.txt : it.page_url);
        a.href = href || "#";
        a.target = "_blank";
        li.appendChild(a);
        if (it.source) {
          const small = document.createElement("small");
          small.style.marginLeft = "8px";
          small.textContent = `(${it.source})`;
          li.appendChild(small);
        }
        ul.appendChild(li);
      });
      sec.appendChild(ul);
      container.appendChild(sec);
    });
  } catch (e) {
    container.textContent = "Failed to load news.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadAnswers();
  loadNews();

  // Optional: dropdown copy helper
  const sel = document.getElementById("samples");
  const btn = document.getElementById("copyQ");
  if (sel && btn) {
    btn.addEventListener("click", async () => {
      const q = sel.value || "";
      if (!q) return;
      await navigator.clipboard.writeText(q);
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = "Copy to clipboard"), 1200);
    });
  }
});
