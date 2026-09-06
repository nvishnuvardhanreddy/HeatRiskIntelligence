(function () {
  const map = L.map("map").setView([22.5, 79], 4.5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);

  async function riskPopup(marker, location) {
    marker.bindPopup("Loading live risk…").openPopup();
    try {
      const data = await GZ.get("/api/risk/current/", location);
      marker.setPopupContent(
        `<strong>${data.location.name || "Selected location"}</strong><br>` +
        `HTSI ${data.risk.score} · ${data.risk.band}<br>` +
        `<small>REAL DATA + CALCULATED</small>`
      );
    } catch (error) {
      marker.setPopupContent(`Live risk unavailable: ${error.message}`);
    }
  }

  const loc = GZ.getLocation();
  if (loc) {
    map.setView([loc.latitude, loc.longitude], 9);
    const marker = L.marker([loc.latitude, loc.longitude]).addTo(map);
    riskPopup(marker, loc);
  }

  map.on("click", (event) => {
    const location = GZ.locationFromCoords(event.latlng.lat, event.latlng.lng);
    GZ.setLocation(location);
    const marker = L.marker(event.latlng).addTo(map);
    riskPopup(marker, location);
  });
})();
