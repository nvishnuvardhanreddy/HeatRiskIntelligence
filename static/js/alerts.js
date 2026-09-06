(async function () {
  const loc = GZ.getLocation(); if (!loc) return;
  try { const data = await GZ.get("/api/risk/current/", loc), risk = data.risk; document.getElementById("alerts-output").innerHTML = risk.score >= 41 ? `<p class="eyebrow">${risk.band} HEAT RISK</p><h2>${data.location.name}</h2><p>Calculated HTSI is ${risk.score}. Take precautions during periods of highest thermal stress.</p><small class="status calculated">CALCULATED · ${risk.label}</small>` : "<h2>No elevated alert threshold</h2><p>Continue ordinary heat-safety precautions and monitor the forecast.</p>"; } catch (e) { document.getElementById("alerts-output").textContent = e.message; }
})();
