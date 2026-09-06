(async function () {
  const loc = GZ.getLocation(); if (!loc) return;
  try { const data = await GZ.get("/api/risk/current/", loc); document.getElementById("worker-risk").textContent = `${data.thermal.htsi.score} · ${data.thermal.htsi.band}`; const hourly = await GZ.get("/api/weather/hourly/", loc); const peak = (hourly.hourly || []).reduce((a, b) => Number(b.temperature) > Number(a.temperature) ? b : a); document.getElementById("worker-peak").textContent = peak ? String(peak.timestamp).replace("T", " ").slice(0, 16) : "Unavailable"; } catch (e) { document.getElementById("worker-risk").textContent = e.message; }
})();

