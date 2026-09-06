(async function () {
  const loc = GZ.getLocation(); if (!loc) return;
  try {
    const data = await GZ.get("/api/weather/hourly/", loc), rows = (data.hourly || []).slice(0, 48);
    const body = document.getElementById("hourly-table");
    body.innerHTML = rows.map(row => `<tr><td>${String(row.timestamp).replace("T", " ").slice(0, 16)}</td><td>${GZ.number(row.temperature, "°C")}</td><td>${GZ.number(row.humidity, "%")}</td><td>${row.thermal ? GZ.number(row.thermal.wbgt, "°C") : "—"}</td><td>${row.thermal ? `${row.thermal.htsi.score} · ${row.thermal.htsi.band}` : "—"}</td><td><span class="status forecast">${row.status}</span></td></tr>`).join("");
    if (rows.length) { const peak = rows.reduce((a, b) => (b.thermal?.htsi?.score || 0) > (a.thermal?.htsi?.score || 0) ? b : a); document.getElementById("peak-period").textContent = `Peak heat stress near ${String(peak.timestamp).replace("T", " ").slice(0, 16)} · HTSI ${peak.thermal?.htsi?.score ?? "unavailable"} (${peak.thermal?.htsi?.band ?? "data quality note"}).`; }
  } catch (e) { document.getElementById("peak-period").textContent = e.message; }
})();
