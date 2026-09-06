(function () {
  const map = L.map("map").setView([22.5, 79], 4.5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap contributors", maxZoom: 18 }).addTo(map);
  const loc = GZ.getLocation();
  if (loc) { map.setView([loc.latitude, loc.longitude], 9); L.marker([loc.latitude, loc.longitude]).addTo(map).bindPopup("Selected location").openPopup(); }
  map.on("click", e => { GZ.setLocation(GZ.locationFromCoords(e.latlng.lat, e.latlng.lng)); L.marker(e.latlng).addTo(map).bindPopup("Location selected — open Dashboard to load live weather.").openPopup(); });
})();

