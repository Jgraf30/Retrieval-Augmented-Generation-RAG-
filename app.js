async function load() {
  try {
    const r = await fetch("answers.json", {cache:"no-store"});
    if (!r.ok) throw new Error("answers.json not found");
    const data = await r.json();

    document.getElementById("q").textContent = data.question || "(no question)";
    document.getElementById("ans").textContent = data.result?.answer || "(no answer)";

    const meta = document.getElementById("meta");
    meta.innerHTML = `<small>Top-K: ${data.top_k ?? "?"}</small>`;

    const list = document.getElementById("srcs");
    list.innerHTML = "";
    (data.result?.sources || []).forEach(s => {
      const li = document.createElement("li");
      li.textContent = `[${s.rank}] ${s.source} (score ${Number(s.score).toFixed(3)})`;
      list.appendChild(li);
    });
  } catch (e) {
    document.body.innerHTML = `<p style="color:#f87171">Failed to load answers.json: ${e.message}</p>`;
  }
}
document.addEventListener("DOMContentLoaded", load);
