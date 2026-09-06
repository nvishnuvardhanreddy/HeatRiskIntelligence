(function () {
  const key = "ground-zero-location";
  window.GZ = {
    getLocation() {
      try { return JSON.parse(localStorage.getItem(key) || "null"); } catch (_) { return null; }
    },
    setLocation(location) {
      localStorage.setItem(key, JSON.stringify(location));
      window.dispatchEvent(new CustomEvent("gz-location", { detail: location }));
    },
    query(location, extra) {
      const params = new URLSearchParams({ lat: location.latitude, lon: location.longitude, ...(extra || {}) });
      return params.toString();
    },
    async get(path, location, extra) {
      const response = await fetch(path + "?" + this.query(location, extra), { headers: { Accept: "application/json" } });
      let body;
      try { body = await response.json(); } catch (_) { throw new Error("The service returned an unreadable response."); }
      if (!response.ok) throw new Error(body.error || "The service did not return data.");
      return body;
    },
    number(value, suffix) { return value === null || value === undefined ? "—" : `${Number(value).toFixed(1)}${suffix || ""}`; },
    wind(value) { return value === null || value === undefined ? "—" : `${(Number(value) * 3.6).toFixed(1)} km/h`; },
    locationFromCoords(latitude, longitude) { return { latitude: Number(latitude), longitude: Number(longitude), name: "Selected location", admin_area: "", country: "" }; }
  };
  document.querySelector(".menu-button")?.addEventListener("click", function () {
    const nav = document.querySelector(".topnav");
    nav.classList.toggle("open");
    this.setAttribute("aria-expanded", nav.classList.contains("open"));
  });
})();
