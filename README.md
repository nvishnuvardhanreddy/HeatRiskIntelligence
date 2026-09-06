# GROUND ZERO

GROUND ZERO is a public-access Django MVP for heatwave early warning and human thermal-stress screening. It uses live Open-Meteo weather and geocoding services (no API key), validates provider data, calculates Heat Index/WBGT/UTCI/HTSI, and labels each value as `LIVE`, `FORECAST`, `CALCULATED`, `ESTIMATED`, or `MODEL ESTIMATE`.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py test
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Use Detect my location, search, or enter latitude/longitude. Weather failures are shown as an error; no fake weather values are substituted.

## Configuration

SQLite is the default. Set `DATABASE_URL=postgresql://...` and optionally `DB_ENGINE=django.contrib.gis.db.backends.postgis` for a PostgreSQL deployment. `REDIS_URL` is reserved for adding Celery/cache workers; the request path remains usable without Redis for an easy local run.

The thermal engine is deliberately transparent: outdoor WBGT uses an estimated globe temperature when a provider does not supply one, and UTCI is a documented screening approximation. The health signal is a baseline planning estimate, not a clinical or mortality prediction.

