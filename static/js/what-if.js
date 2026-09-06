(function () {
  const form = document.getElementById("what-if-form"), result = document.getElementById("scenario-result"), error = document.getElementById("scenario-error");
  if (!form) return;
  form.addEventListener("submit", async function (event) {
    event.preventDefault(); error.hidden = true;
    const params = new URLSearchParams(new FormData(form));
    try {
      const response = await fetch("/api/what-if/?" + params, { headers: { Accept: "application/json" } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Scenario calculation failed.");
      const t = data.thermal, risk = data.risk;
      result.innerHTML = `<article class="panel risk-summary"><div><p class="eyebrow">SIMULATED RESULT</p><h2>${risk.band}</h2><p>${data.disclaimer}</p></div><strong>${Number(risk.score).toFixed(1)}</strong></article><div class="metric-grid scenario-metrics"><article class="metric"><span>Heat Index</span><strong>${Number(t.heat_index).toFixed(1)} °C</strong></article><article class="metric"><span>WBGT</span><strong>${Number(t.wbgt).toFixed(1)} °C</strong></article><article class="metric"><span>UTCI</span><strong>${Number(t.utci).toFixed(1)} °C</strong></article><article class="metric"><span>HTSI</span><strong>${Number(risk.score).toFixed(1)} · ${risk.band}</strong></article></div>`;
    } catch (exception) { error.textContent = exception.message; error.hidden = false; }
  });
})();
