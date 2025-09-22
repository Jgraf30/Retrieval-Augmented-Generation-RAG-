function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

async function loadAnswers() {
  try {
    const r = await fetch("answers.json", { cache: "no-store" });
    if (!r.ok) throw new Error("answers.json missing");
    const data = await r.json();

    // Support BOTH schemas: flat (question/answer/sources) and old nested (result.answer)
    const question = data.question || "(no question)";
    const answerRaw = (typeof data.answer === "string" && data.answer.length)
      ? data.answer
      : (data.result && typeof data.result.answer === "string" ? data.result.answer : "");

    const sources = Array.isArray(data.sources) ? data.sources
      : (data.result && Array.isArray(data.result.sources) ? data.result.sources : []);

    // Render question
    const qEl = document.getElementById("q");
    if (qEl) qEl.textContent = question;

    // Render answer with preserved line breaks
    const aEl = document.getElementById("ans");
    if (aEl) {
      if (answerRaw) {
        aEl.innerHTML = escapeHtml(answerRaw).replace(/\n/g, "<br/>");
      } else {
        aEl.textContent = "(no answer)";
      }
    }

    // Render sources
    const list = document.getElementById("srcs");
    if (list) {
      list.innerHTML = "";
      sources.forEach(s => {
        const li = document.createElement("li");
        const rank = s.rank != null ? s.rank : "?";
        const score = (typeof s.score === "number") ? ` (score ${Number(s.score).toFixed(3)})` : "";
        const begin = (typeof s.begin === "number") ? `, begin ${s.begin}` : "";
        const end = (typeof s.end === "number") ? `, end ${s.end}` : "";
        li.textContent = `[${rank}] ${s.source || "(unknown source)"}${score}${begin}${end}`;
        list.appendChild(li);
      });
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
    if (!r.ok) { container.textContent = "No news manifest yet."; return; }
    const data = await r.json();
    const batches = (data.batches || []).slice(-3).reverse();
    if (batches.length === 0) { container.textContent = "No recent articles yet."; return; }
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
        const href = it.files?.pdf ? it.files.pdf : (it.files?.txt ? it.files.txt : it.page_url);
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
  } catch {
    container.textContent = "Failed to load news.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadAnswers();
  loadNews();
});
