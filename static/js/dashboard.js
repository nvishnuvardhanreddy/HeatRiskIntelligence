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
      renderPopulation(current.population || {});
      const nearby = await GZ.get("/api/risk/nearby/", location);
      renderNearby(nearby);
      const forecast = await GZ.get("/api/weather/forecast/", location);
      renderForecast(forecast.forecast || []);
      $("location-message").textContent = "Updated from the live provider.";
    } catch (error) {
      showError(error.message + " Live weather data is not replaced with demo values.");
      $("location-message").textContent = "Try another location or try again shortly.";
    }
    function renderNearby(data) {
      const areas = data.areas || [], district = data.district || {};
      areas.slice(0, 2).forEach((area, index) => {
        const rank = index + 2;
        if ($(`nearby-area-${rank}`)) $(`nearby-area-${rank}`).textContent = area.area;
        if ($(`nearby-score-${rank}`)) $(`nearby-score-${rank}`).textContent = `HTSI ${area.htsi}`;
        if ($(`nearby-risk-${rank}`)) $(`nearby-risk-${rank}`).textContent = `${area.risk} · ${area.priority} PRIORITY`;
        if ($(`nearby-population-${rank}`)) $(`nearby-population-${rank}`).textContent = Number(area.population).toLocaleString("en-IN");
        if ($(`nearby-distance-${rank}`)) $(`nearby-distance-${rank}`).textContent = `${area.distance_km} km`;
      });
      if ($("district-name")) $("district-name").textContent = district.name || "District context";
      if ($("district-score")) $("district-score").textContent = `HTSI ${district.average_htsi ?? "—"}`;
      if ($("district-risk")) $("district-risk").textContent = district.risk || "Awaiting location";
      if ($("district-population")) $("district-population").textContent = Number(district.population || 0).toLocaleString("en-IN");
      if ($("district-high-risk")) $("district-high-risk").textContent = district.high_risk_areas ?? "—";
    }
    function renderPopulation(data) {
      const value = data.population === null || data.population === undefined ? "Select a location" : Number(data.population).toLocaleString("en-IN");
      if ($("decision-population")) $("decision-population").textContent = value;
      if ($("population-source")) $("population-source").textContent = data.status || "ESTIMATED";
      if ($("priority-population")) $("priority-population").textContent = value;
      if ($("worker-population")) $("worker-population").textContent = data.outdoor_worker_population ? Number(data.outdoor_worker_population).toLocaleString("en-IN") : value;
      if ($("vulnerable-population")) $("vulnerable-population").textContent = data.elderly_children_population ? Number(data.elderly_children_population).toLocaleString("en-IN") : value;
      if ($("overview-worker-population")) $("overview-worker-population").textContent = data.outdoor_worker_population ? Number(data.outdoor_worker_population).toLocaleString("en-IN") : value;
      if ($("overview-vulnerable-population")) $("overview-vulnerable-population").textContent = data.elderly_children_population ? Number(data.elderly_children_population).toLocaleString("en-IN") : value;
    }
  }
  function renderCurrent(data) {
    const w = data.weather, t = data.thermal, loc = data.location;
    $("location-name").textContent = loc.name || "Selected location";
    if ($("location-state")) $("location-state").textContent = [loc.admin_area, loc.country].filter(Boolean).join(" · ") || "Area identified from coordinates";
    if ($("location-district")) $("location-district").textContent = loc.district || "Regional area";
    if ($("location-latitude")) $("location-latitude").textContent = `${Number(loc.latitude).toFixed(4)}°`;
    if ($("location-longitude")) $("location-longitude").textContent = `${Number(loc.longitude).toFixed(4)}°`;
    $("location-detail").textContent = `Location source: ${loc.source || "backend geocoding"}`;
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
    if ($("wind-direction")) $("wind-direction").textContent = GZ.number(w.wind_direction, "°");
    if ($("pressure")) $("pressure").textContent = GZ.number(w.pressure, " hPa");
    if ($("cloud-cover")) $("cloud-cover").textContent = GZ.number(w.cloud_cover, "%");
    if ($("uv-index")) $("uv-index").textContent = GZ.number(w.uv_index, "");
    $("heat-index").textContent = GZ.number(t.heat_index, "°C");
    $("wbgt").textContent = GZ.number(t.wbgt, "°C");
    $("utci").textContent = GZ.number(t.utci, "°C");
    if ($("health-summary")) $("health-summary").textContent = `Health-risk score ${data.health.score} · ${data.health.band}. Calculated planning signal.`;
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
    const band = data.risk.band, score = Number(t.htsi.score);
    const response = score >= 81 ? "EMERGENCY" : score >= 61 ? "ACTION" : score >= 41 ? "ADVISORY" : score >= 21 ? "WATCH" : "NORMAL";
    if ($("response-level")) $("response-level").textContent = `RESPONSE LEVEL · ${response}`;
    if ($("decision-htsi")) $("decision-htsi").textContent = score;
    if ($("decision-health")) $("decision-health").textContent = `${GZ.number(data.health.score, "")} / 100 · CALCULATED`;
    if ($("decision-hospital")) $("decision-hospital").textContent = `${GZ.number(data.health.hospital_impact, "")} / 100`;
    if ($("decision-mortality")) $("decision-mortality").textContent = `${GZ.number(data.health.mortality, "")} / 100`;
    if ($("health-score")) $("health-score").textContent = `${GZ.number(data.health.score, "")} / 100`;
    if ($("health-exposure")) $("health-exposure").textContent = `${GZ.number(data.health.exposure, "")} / 100`;
    if ($("health-vulnerability")) $("health-vulnerability").textContent = `${GZ.number(data.health.vulnerability, "")} / 100`;
    if ($("health-pressure")) $("health-pressure").textContent = `${GZ.number(data.health.hospital_impact, "")} / 100`;
    if ($("priority-location")) $("priority-location").textContent = loc.name || "Selected area";
    if ($("priority-score")) $("priority-score").textContent = score;
    if ($("priority-band")) $("priority-band").textContent = band;
    if ($("worker-risk")) $("worker-risk").textContent = band;
    if ($("vulnerable-risk")) $("vulnerable-risk").textContent = band;
    const priorityLabel = score >= 61 ? "HIGH PRIORITY" : score >= 41 ? "MODERATE PRIORITY" : "LOW PRIORITY";
    if ($("worker-priority")) $("worker-priority").textContent = priorityLabel;
    if ($("vulnerable-priority")) $("vulnerable-priority").textContent = priorityLabel;
    if ($("overview-worker-risk")) $("overview-worker-risk").textContent = band;
    if ($("overview-vulnerable-risk")) $("overview-vulnerable-risk").textContent = band;
    if ($("overview-worker-priority")) $("overview-worker-priority").textContent = priorityLabel;
    if ($("overview-vulnerable-priority")) $("overview-vulnerable-priority").textContent = priorityLabel;
    if ($("action-plan")) {
      const urgent = score >= 61;
      const actions = [
        ["Monitor thermal conditions", urgent ? "RECOMMENDED" : "STANDBY"],
        ["Promote hydration and cooling breaks", score >= 21 ? "RECOMMENDED" : "STANDBY"],
        ["Verify drinking-water supply", score >= 41 ? "RECOMMENDED" : "STANDBY"],
        ["Prioritise vulnerable-population checks", score >= 41 ? "RECOMMENDED" : "STANDBY"],
        ["Adjust outdoor-work hours", score >= 61 ? "RECOMMENDED" : "STANDBY"],
      ];
      $("action-plan").innerHTML = actions.map((item, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span>${item[0]} <b>${item[1]}</b></li>`).join("");
    }
    if ($("intervention-triggers")) {
      $("intervention-triggers").innerHTML = `<div><strong>THERMAL RISK</strong><span>${band} · HTSI ${score}</span></div><div><strong>EXPOSURE</strong><span>${GZ.number(data.health.exposure, "")} / 100 · CALCULATED</span></div><div><strong>VULNERABILITY</strong><span>${GZ.number(data.health.vulnerability, "")} / 100 · CALCULATED</span></div>`;
    }
    const driverValues = {
      temperature: Math.max(0, Math.min(100, (Number(w.temperature) - 20) * 4)),
      humidity: Number(w.humidity),
      wind: Math.max(0, Math.min(100, 100 - Number(w.wind_speed) * 12)),
      solar: Math.max(0, Math.min(100, Number(w.solar_radiation) / 10))
    };
    [["temperature", GZ.number(w.temperature, "°C")], ["humidity", GZ.number(w.humidity, "%")],
      ["wind", GZ.wind(w.wind_speed)], ["solar", GZ.number(w.solar_radiation, " W/m²")]].forEach(([name, value]) => {
      if ($(`driver-${name}`)) $(`driver-${name}`).textContent = value;
      if ($(`driver-${name}-bar`)) $(`driver-${name}-bar`).style.width = `${driverValues[name]}%`;
    });
    if ($("driver-summary")) {
      $("driver-summary").textContent = `${t.htsi.band} risk reflects temperature, humidity, wind and solar exposure at the selected location.`;
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
