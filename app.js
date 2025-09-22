// app.js — full file

// -------- utilities --------
function escapeHtml(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function byId(id){return document.getElementById(id);}

function renderEntry(entry){
  const qEl   = byId("q");
  const aEl   = byId("ans");
  const list  = byId("srcs");
  const meth  = byId("method");
  const stamp = byId("stamp");

  const question = entry.question || "(no question)";
  const answer   = (entry.answer && entry.answer.trim()) ? entry.answer : "(no answer)";
  const sources  = Array.isArray(entry.sources) ? entry.sources : [];

  if (qEl) qEl.textContent = question;
  if (aEl) aEl.innerHTML = escapeHtml(answer).replace(/\n/g,"<br/>");

  if (list){
    list.innerHTML = "";
    sources.forEach(s=>{
      const li = document.createElement("li");
      const rank  = (s.rank!=null)? s.rank : "?";
      const score = (typeof s.score==="number") ? ` (score ${Number(s.score).toFixed(3)})` : "";
      const begin = (typeof s.begin==="number") ? `, begin ${s.begin}` : "";
      const end   = (typeof s.end==="number")   ? `, end ${s.end}`     : "";
      li.textContent = `[${rank}] ${s.source||"(unknown)"}${score}${begin}${end}`;
      list.appendChild(li);
    });
  }

  if (meth)  meth.textContent  = entry.method ? `Method: ${entry.method}` : "";
  if (stamp && entry.updated_at){
    const dt = new Date(entry.updated_at * 1000);
    stamp.textContent = `Updated ${dt.toLocaleString()}`;
  }
}

// Try loading multi-answers first; if unavailable, fall back to single answers.json
async function loadMultiMode(){
  const resQ = await fetch("questions.json", {cache:"no-store"});
  const resA = await fetch("answers_multi.json", {cache:"no-store"});
  if (!resQ.ok || !resA.ok) return null;

  const questions = await resQ.json();
  const entries   = await resA.json();
  if (!Array.isArray(questions) || !Array.isArray(entries) || questions.length===0 || entries.length===0) return null;

  // populate dropdown
  const sel = byId("questionSelect");
  if (sel){
    sel.innerHTML = "";
    questions.forEach((q,i)=>{
      const opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = q;
      sel.appendChild(opt);
    });
  }

  // pick first question entry
  const firstQ = questions[0];
  let current = entries.find(e => (e.question||"")===firstQ) || entries[0];
  renderEntry(current);

  // wire change
  if (sel){
    sel.addEventListener("change", ()=>{
      const idx = Number(sel.value);
      const q   = questions[idx] || "";
      const match = entries.find(e => (e.question||"")===q);
      renderEntry(match || entries[0]);
    });
  }

  return {questions, entries};
}

async function loadSingleMode(){
  const r = await fetch("answers.json", {cache:"no-store"});
  if (!r.ok) return null;
  const raw = await r.json();

  // tolerate both flat and nested schemas
  const question = raw.question || "(no question)";
  const answer   = (typeof raw.answer==="string" && raw.answer.length)
                 ? raw.answer
                 : (raw.result && typeof raw.result.answer==="string" ? raw.result.answer : "(no answer)");
  const sources  = Array.isArray(raw.sources) ? raw.sources
                 : (raw.result && Array.isArray(raw.result.sources) ? raw.result.sources : []);
  const method   = raw.method || "";
  const updated  = raw.updated_at || (raw.result && raw.result.updated_at) || null;

  renderEntry({question, answer, sources, method, updated_at: updated});
  return {question, answer, sources};
}

// Very lightweight news loader (safe if no manifest exists)
async function loadNews(){
  const container = byId("news"); if(!container) return;
  try{
    const r = await fetch("data/news/manifest.json", {cache:"no-store"});
    if(!r.ok){container.textContent="No news manifest yet.";return;}
    const data = await r.json();
    const batches = (data.batches||[]).slice(-3).reverse();
    if(!batches.length){container.textContent="No recent articles yet.";return;}
    container.innerHTML="";
    batches.forEach(b=>{
      const sec = document.createElement("div"); sec.className="news-batch";
      const h   = document.createElement("h3"); h.textContent=`Batch ${b.date} — ${b.count} item(s)`; sec.appendChild(h);
      const ul  = document.createElement("ul");
      (b.items||[]).forEach(it=>{
        const li = document.createElement("li");
        const a  = document.createElement("a");
        a.textContent = it.title || "(untitled)";
        const href = it.files?.pdf || it.files?.txt || it.page_url;
        a.href = href || "#"; a.target = "_blank";
        li.appendChild(a);
        if (it.source){
          const sm = document.createElement("small");
          sm.style.marginLeft="8px"; sm.textContent = `(${it.source})`;
          li.appendChild(sm);
        }
        ul.appendChild(li);
      });
      sec.appendChild(ul); container.appendChild(sec);
    });
  }catch{
    container.textContent = "Failed to load news.";
  }
}

// Main init
document.addEventListener("DOMContentLoaded", async ()=>{
  // Refresh button
  const btn = byId("refresh");
  if (btn) btn.addEventListener("click", ()=>location.reload());

  // Try multi mode first, then single
  const multi = await loadMultiMode();
  if (!multi) await loadSingleMode();

  // News (optional)
  loadNews();
});
