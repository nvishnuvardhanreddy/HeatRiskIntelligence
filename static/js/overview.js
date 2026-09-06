(function () {
  const mapElement = document.getElementById("overview-map");
  if (window.L && mapElement) {
    const map = L.map(mapElement, { scrollWheelZoom: false }).setView([22.5, 79], 4.5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 12,
    }).addTo(map);
    const location = GZ.getLocation();
    if (location) {
      map.setView([location.latitude, location.longitude], 8);
      L.marker([location.latitude, location.longitude]).addTo(map).bindPopup("Selected location");
    }
  }
  ["overview-detect", "overview-detect-bottom"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      if (!navigator.geolocation) {
        document.getElementById("overview-status").textContent = "GPS is unavailable. Use the dashboard search instead.";
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          GZ.setLocation(GZ.locationFromCoords(position.coords.latitude, position.coords.longitude));
          window.location.href = "/dashboard/";
        },
        () => {
          document.getElementById("overview-status").textContent = "Location permission was unavailable. Use the dashboard search instead.";
        },
        { enableHighAccuracy: false, timeout: 10000 }
      );
    });
  });
})();
