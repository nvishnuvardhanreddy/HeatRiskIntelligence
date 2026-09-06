(async function () {
  const loc = GZ.getLocation(); if (!loc) return;
  try {
    const data = await GZ.get("/api/risk/current/", loc), w = data.weather, t = data.thermal;
    const values = [["Temperature", GZ.number(w.temperature, "°C")], ["Humidity", GZ.number(w.humidity, "%")], ["Wind", GZ.wind(w.wind_speed)], ["Solar radiation", GZ.number(w.solar_radiation, " W/m²")], ["Pressure", GZ.number(w.pressure, " hPa")], ["Cloud cover", GZ.number(w.cloud_cover, "%")]];
    document.getElementById("atmospheric-list").innerHTML = values.map(v => `<dt>${v[0]}</dt><dd>${v[1]}</dd>`).join("");
    document.getElementById("analysis-hi").textContent = GZ.number(t.heat_index, "°C");
    document.getElementById("analysis-wbgt").textContent = GZ.number(t.wbgt, "°C");
    document.getElementById("analysis-utci").textContent = GZ.number(t.utci, "°C");
    document.getElementById("analysis-reasons").innerHTML = (data.risk.reason || []).map(reason => `<li>${reason}</li>`).join("");
  } catch (e) { document.querySelector(".notice").textContent = e.message; }
})();
