(function () {
  const key = "ground-zero-location";

  /**
   * Compute true solar elevation angle (radians) for a given local datetime and
   * coordinates.  Uses the Spencer (1971) equation of time and a longitude-based
   * UTC-offset correction so that solar noon is accurate regardless of timezone.
   */
  function solarElevation(dateObj, lat, lon) {
    const latR = lat * Math.PI / 180;
    const doy = Math.floor((dateObj - new Date(dateObj.getFullYear(), 0, 0)) / 86400000);
    // UTC offset from the JS date object (minutes → hours).
    const utcOffsetH = -dateObj.getTimezoneOffset() / 60;
    const localH = dateObj.getHours() + dateObj.getMinutes() / 60 + dateObj.getSeconds() / 3600;
    const stdMeridian = Math.round(utcOffsetH) * 15;
    const lonCorrection = (lon - stdMeridian) / 15; // hours
    const bRad = (360 / 365 * (doy - 81)) * Math.PI / 180;
    const eot = 9.87 * Math.sin(2 * bRad) - 7.53 * Math.cos(bRad) - 1.5 * Math.sin(bRad); // minutes
    const solarTime = localH + lonCorrection + eot / 60;
    const decl = 23.45 * Math.sin((360 / 365 * (284 + doy)) * Math.PI / 180) * Math.PI / 180;
    const ha = (15 * (solarTime - 12)) * Math.PI / 180;
    return Math.asin(Math.sin(latR) * Math.sin(decl) + Math.cos(latR) * Math.cos(decl) * Math.cos(ha));
  }

  /**
   * Estimate solar radiation and UV.
   * Uses is_day (Open-Meteo flag) as the authoritative daytime signal.
   * Falls back to true solar elevation angle (−3° civil twilight buffer).
   * Returns { value, status } for both solar and UV.
   */
  function daylightEstimate(timestamp, solar, cloud, isDay, lat, lon) {
    // If API already returned a positive value, use it directly.
    if (Number(solar) > 0) return { value: Number(solar), status: "LIVE" };

    // Determine whether it is currently daytime.
    let daytime = false;
    if (isDay !== undefined && isDay !== null) {
      daytime = Boolean(isDay); // authoritative Open-Meteo flag
    } else {
      try {
        const when = new Date(String(timestamp).replace(" ", "T"));
        if (Number.isFinite(when.getTime()) && lat !== undefined && lon !== undefined) {
          const elev = solarElevation(when, Number(lat), Number(lon));
          daytime = elev > (-3 * Math.PI / 180); // civil twilight buffer
        }
      } catch (_) { /* leave daytime = false */ }
    }

    if (!daytime) return { value: 0, status: "LIVE" };

    // Estimate clear-sky irradiance attenuated by cloud cover.
    try {
      const when = new Date(String(timestamp).replace(" ", "T"));
      if (!Number.isFinite(when.getTime())) return { value: 0, status: "LIVE" };
      const elev = solarElevation(when, Number(lat), Number(lon));
      if (elev <= 0) return { value: 0, status: "LIVE" };
      const airMass = 1 / Math.max(0.1, Math.sin(elev));
      const clearSky = 1361 * Math.sin(elev) * Math.exp(-0.14 * airMass);
      const cloudPct = Math.max(0, Math.min(100, Number(cloud) || 0));
      const transmission = 1 - 0.75 * Math.pow(cloudPct / 100, 3);
      const value = Math.round(Math.max(0, clearSky * transmission) * 10) / 10;
      return { value, status: "ESTIMATED" };
    } catch (_) {
      return { value: 0, status: "LIVE" };
    }
  }

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
    async getBrowserLiveWeather(location) {
      const params = new URLSearchParams({
        latitude: location.latitude, longitude: location.longitude, timezone: "auto",
        // is_day added so the browser fallback can detect nighttime authoritatively.
        current: "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,shortwave_radiation,surface_pressure,cloud_cover,precipitation,uv_index,dew_point_2m,is_day",
        daily: "temperature_2m_min,temperature_2m_max,relative_humidity_2m_mean,wind_speed_10m_max,shortwave_radiation_sum,precipitation_sum,uv_index_max",
        forecast_days: "6"
      });
      const response = await fetch("https://api.open-meteo.com/v1/forecast?" + params.toString(), { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Browser live weather request failed.");
      const payload = await response.json();
      const current = payload.current || {};
      const daily = payload.daily || {};
      const lat = location.latitude, lon = location.longitude;
      const solar = daylightEstimate(current.time, current.shortwave_radiation, current.cloud_cover, current.is_day, lat, lon);
      const liveUv = Number(current.uv_index);
      const uv = liveUv > 0 ? { value: liveUv, status: "LIVE" } : { value: Math.min(11, solar.value / 100), status: solar.status };
      console.info("[GROUND ZERO] Browser weather fields:", {
        solar: solar.status, uv: uv.status, solarRadiation: solar.value, uvIndex: uv.value, isDay: current.is_day
      });
      const weather = {
        timestamp: current.time, temperature: current.temperature_2m,
        humidity: current.relative_humidity_2m, apparent_temperature: current.apparent_temperature,
        wind_speed: Number(current.wind_speed_10m || 0) / 3.6, wind_speed_unit: "m/s",
        wind_direction: current.wind_direction_10m, solar_radiation: solar.value,
        pressure: current.surface_pressure, cloud_cover: current.cloud_cover,
        precipitation: current.precipitation, uv_index: Math.round(uv.value * 10) / 10,
        dew_point: current.dew_point_2m, source: "Open-Meteo browser live",
        solar_status: solar.status, uv_status: uv.status, data_mode: "BROWSER_LIVE"
      };
      const thermal = await this.get("/api/what-if/", location, {
        temperature: weather.temperature, humidity: weather.humidity,
        wind_speed: weather.wind_speed, solar_radiation: weather.solar_radiation
      });
      const score = Number(thermal.risk.score);
      const health = { score, band: thermal.risk.band, label: "CALCULATED",
        exposure: Math.min(100, score * .75 + weather.humidity * .15 + Math.max(0, 10 - weather.wind_speed)),
        vulnerability: score, hospital_impact: score, mortality: score, priority: score };
      const forecast = (daily.time || []).slice(0, 5).map((date, index) => ({
        date, temperature_min: daily.temperature_2m_min[index], temperature_max: daily.temperature_2m_max[index],
        humidity: daily.relative_humidity_2m_mean[index], wind_speed: Number(daily.wind_speed_10m_max[index] || 0) / 3.6,
        solar_radiation: Number(daily.shortwave_radiation_sum[index] || 0) * 1000000 / 86400,
        precipitation: daily.precipitation_sum[index] || 0, source: "Open-Meteo browser live"
      }));
      return { weather, thermal: thermal.thermal, risk: { score, band: thermal.risk.band, reason: [] },
        health, forecast, data_mode: "BROWSER_LIVE" };
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
