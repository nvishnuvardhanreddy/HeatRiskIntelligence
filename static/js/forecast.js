(async function () {
  const loc = GZ.getLocation(), container = document.getElementById("forecast-table"); if (!loc) return;
  try {
    const data = await GZ.get("/api/weather/forecast/", loc), rows = data.forecast || [];
    if (data.anomalies?.length) { const alert = document.getElementById("forecast-alert"); alert.hidden = false; alert.className = "notice info"; alert.textContent = "Data quality note: " + data.anomalies.join(" "); }
    container.innerHTML = rows.map(r => `<article class="forecast-card"><h2>${r.date}</h2><p>Min / max</p><div class="max">${GZ.number(r.temperature_min, "°")} / ${GZ.number(r.temperature_max, "°")}</div><dl><dt>Humidity</dt><dd>${GZ.number(r.humidity, "%")}</dd><dt>Wind</dt><dd>${GZ.wind(r.wind_speed)}</dd><dt>Solar</dt><dd>${GZ.number(r.solar_radiation, " W/m²")}</dd><dt>Heat Index</dt><dd>${GZ.number(r.heat_index, "°")}</dd><dt>WBGT</dt><dd>${GZ.number(r.wbgt, "°")}</dd><dt>UTCI</dt><dd>${GZ.number(r.utci, "°")}</dd><dt>HTSI risk</dt><dd>${r.risk_score} · ${r.risk_band}</dd></dl><small class="status forecast">FORECAST · CALCULATED</small></article>`).join("");
    if (window.Chart) new Chart(document.getElementById("forecast-chart"), { type: "line", data: { labels: rows.map(r => r.date), datasets: [{ label: "Max temperature °C", data: rows.map(r => r.temperature_max), borderColor: "#e86522" }, { label: "HTSI", data: rows.map(r => r.htsi.score), borderColor: "#087f8c" }] }, options: { scales: { y: { beginAtZero: false } } } });
  } catch (e) { container.innerHTML = `<div class="notice error">${e.message}</div>`; }
})();
