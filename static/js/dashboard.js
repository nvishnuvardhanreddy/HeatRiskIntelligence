(function () {
  const $ = id => document.getElementById(id);
  let chart;
  function showError(message) { $("data-error").textContent = message; $("data-error").hidden = false; }
  function clearError() { $("data-error").hidden = true; }
  function select(location) {
    GZ.setLocation(location);
    load(location);
  }
  async function load(location) {
    clearError();
    $("location-message").textContent = "Fetching live weather and forecast…";
    try {
      const current = await GZ.get("/api/risk/current/", location);
      renderCurrent(current);
      const forecast = await GZ.get("/api/weather/forecast/", location);
      renderForecast(forecast.forecast || []);
      $("location-message").textContent = "Updated from the live provider.";
    } catch (error) {
      showError(error.message + " Live weather data is not replaced with demo values.");
      $("location-message").textContent = "Try another location or try again shortly.";
    }
  }
  function renderCurrent(data) {
    const w = data.weather, t = data.thermal, loc = data.location;
    $("location-name").textContent = loc.name || "Selected location";
    $("location-detail").textContent = [loc.admin_area, loc.country, `${Number(loc.latitude).toFixed(4)}°, ${Number(loc.longitude).toFixed(4)}°`].filter(Boolean).join(" · ");
    $("htsi-score").textContent = t.htsi.score;
    $("htsi-band").textContent = t.htsi.band;
    if ($("risk-progress")) $("risk-progress").style.width = `${Math.max(0, Math.min(100, t.htsi.score))}%`;
    $("risk-reason").textContent = (data.risk.reason || []).join(" ");
    $("temperature").textContent = GZ.number(w.temperature, "°C");
    $("apparent-temperature").textContent = GZ.number(w.apparent_temperature, "°C");
    $("humidity").textContent = GZ.number(w.humidity, "%");
    $("wind").textContent = GZ.wind(w.wind_speed);
    $("solar").textContent = GZ.number(w.solar_radiation, " W/m²");
    $("solar-label").textContent = w.solar_status || "LIVE";
    $("heat-index").textContent = GZ.number(t.heat_index, "°C");
    $("wbgt").textContent = GZ.number(t.wbgt, "°C");
    $("utci").textContent = GZ.number(t.utci, "°C");
    if ($("health-summary")) $("health-summary").textContent = `Health-risk score ${data.health.score} · ${data.health.band}. ${data.health.label}.`;
    if ($("health-score")) $("health-score").textContent = `${Number(data.health.score).toFixed(1)} / 100`;
    if ($("health-priority")) $("health-priority").textContent = data.health.band;
    if ($("warning-title")) $("warning-title").textContent = `${data.risk.band} thermal stress`;
    if ($("warning-text")) $("warning-text").textContent = (data.risk.reason || []).join(" ") || "Follow official heat-safety guidance.";
    if ($("alert-area")) $("alert-area").textContent = loc.name || "Selected area";
    if ($("alert-status")) $("alert-status").textContent = `${data.risk.band === "LOW" || data.risk.band === "MODERATE" ? "MONITOR" : "ACTIVE HEAT ALERT"} · CALCULATED`;
    if ($("alert-reason")) $("alert-reason").textContent = (data.risk.reason || []).join(" ") || "No elevated risk drivers identified.";
    if ($("warning-actions")) {
      const actions = data.risk.band === "LOW" ? ["Maintain hydration.", "Use normal heat precautions."] : ["Stay hydrated.", "Reduce prolonged outdoor exposure.", "Take regular breaks.", "Monitor vulnerable people.", "Follow official heat-health advisories."];
      $("warning-actions").innerHTML = actions.map(action => `<li>${action}</li>`).join("");
    }
  }
  function renderForecast(rows) {
    $("forecast-strip").innerHTML = rows.map(row => `<article class="forecast-item"><span>${row.date}</span><strong>${GZ.number(row.temperature_min, "°")} / ${GZ.number(row.temperature_max, "°")}</strong><span>HTSI ${row.htsi.score}</span><span class="band">${row.htsi.band}</span><small class="status forecast">FORECAST · CALCULATED</small></article>`).join("");
    const labels = rows.map(r => r.date), values = rows.map(r => r.htsi.score);
    if ($("risk-trend") && values.length > 1) {
      const delta = values[values.length - 1] - values[0];
      $("risk-trend").textContent = `RISK TREND · ${delta > 3 ? "INCREASING" : delta < -3 ? "IMPROVING" : "STABLE"}`;
    }
    if (window.Chart && $("risk-chart")) {
      chart?.destroy();
      chart = new Chart($("risk-chart"), { type: "line", data: { labels, datasets: [{ label: "HTSI", data: values, borderColor: "#087f8c", backgroundColor: "rgba(8,127,140,.1)", fill: true, tension: .25 }] }, options: { plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } } });
    }
  }
  $("detect-location")?.addEventListener("click", () => {
    if (!navigator.geolocation) { showError("This browser does not provide location detection."); return; }
    $("location-message").textContent = "Requesting browser location permission…";
    navigator.geolocation.getCurrentPosition(
      p => select(GZ.locationFromCoords(p.coords.latitude, p.coords.longitude)),
      () => showError("Location permission was unavailable. Search for a city or enter coordinates instead."),
      { enableHighAccuracy: false, timeout: 10000 }
    );
  });
  $("coordinate-button")?.addEventListener("click", () => {
    const lat = parseFloat($("latitude").value), lon = parseFloat($("longitude").value);
    if (Number.isFinite(lat) && Number.isFinite(lon)) select(GZ.locationFromCoords(lat, lon)); else showError("Enter a valid latitude and longitude.");
  });
  $("search-button")?.addEventListener("click", async () => {
    const query = $("location-search").value.trim(), box = $("search-results");
    const coordinate = query.split(",").map(Number);
    if (coordinate.length === 2 && coordinate.every(Number.isFinite)) { select(GZ.locationFromCoords(coordinate[0], coordinate[1])); return; }
    if (query.length < 2) { showError("Search requires at least two characters."); return; }
    try {
      const response = await fetch("/api/locations/search/?q=" + encodeURIComponent(query));
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      box.innerHTML = (data.results || []).map((item, index) => `<button data-index="${index}">${item.name}, ${item.admin_area || item.country} <small>${Number(item.latitude).toFixed(3)}, ${Number(item.longitude).toFixed(3)}</small></button>`).join("") || "<p class='muted'>No locations found.</p>";
      box.querySelectorAll("button").forEach((button, index) => button.addEventListener("click", () => { const item = data.results[index]; box.innerHTML = ""; select(item); }));
    } catch (error) { showError(error.message); }
  });
  const stored = GZ.getLocation();
  if (stored) load(stored);
})();
