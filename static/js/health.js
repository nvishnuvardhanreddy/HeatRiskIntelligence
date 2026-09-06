(async function () {
  const loc = GZ.getLocation(); if (!loc) return;
  try { const data = await GZ.get("/api/risk/health/", loc); document.getElementById("health-band").textContent = data.band; document.getElementById("health-score").textContent = `${data.score}/100 · CALCULATED`; document.getElementById("health-factors").innerHTML = data.factors.map(f => `<li>${f}</li>`).join(""); } catch (e) { document.getElementById("health-score").textContent = "Select a location to calculate."; }
})();
