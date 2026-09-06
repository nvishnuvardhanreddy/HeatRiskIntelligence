document.getElementById("compare-button")?.addEventListener("click", async () => {
  const output = document.getElementById("compare-output"), names = [document.getElementById("compare-a").value, document.getElementById("compare-b").value];
  output.innerHTML = "<p>Loading live locations…</p>";
  try {
    const cards = await Promise.all(names.map(async name => { const searchResponse = await fetch("/api/locations/search/?q=" + encodeURIComponent(name)); const search = await searchResponse.json(); if (!search.results?.length) throw new Error("Location not found: " + name); const data = await GZ.get("/api/risk/current/", search.results[0]); return `<article class="panel"><h2>${data.location.name}</h2><strong>${data.thermal.htsi.score} · ${data.thermal.htsi.band}</strong><p>${GZ.number(data.weather.temperature, "°C")} · ${GZ.number(data.thermal.wbgt, "°C WBGT")}</p><small class="status live">LIVE · CALCULATED</small></article>`; }));
    output.innerHTML = cards.join("");
  } catch (e) { output.innerHTML = `<div class="notice error">${e.message}</div>`; }
});

