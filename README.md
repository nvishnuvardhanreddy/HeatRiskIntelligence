# Ground Zero

Ground Zero is a Django heat-risk dashboard for public heat-safety planning. It
uses live [Open-Meteo](https://open-meteo.com/) weather and geocoding, then
calculates Heat Index, WBGT, UTCI and the transparent Human Thermal Stress
Index (HTSI). Provider failures are shown to the user; weather is never
replaced with demo values.

## Local development

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The primary navigation is Overview, Dashboard,
What-If Simulation, Forecast, Alerts and GPS Location. The simulation is
explicitly labelled `SIMULATED` and does not pretend to be observed weather.

## Project structure

```text
config/                 settings, URLs, WSGI/ASGI and Celery setup
core/                   pages, JSON APIs, models, migrations and tests
services/               weather orchestration, locations, solar and risk
weather/providers/      Open-Meteo provider contract and implementation
thermal/                Heat Index, WBGT, UTCI and HTSI calculations
ml_models/              optional model seam, metadata and train.py pipeline
templates/               Django templates (vanilla JS UI)
static/css, static/js/   dark dashboard styles and progressive-enhancement JS
build.sh, render.yaml    Render build/start/health deployment configuration
```

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django signing key; set a secret in production |
| `DEBUG` | `0` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `RENDER_EXTERNAL_HOSTNAME` | Optional Render-provided hostname, added automatically to allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins |
| `DATABASE_URL` | PostgreSQL URL; absent means local SQLite |
| `DB_ENGINE` | Optional PostgreSQL/PostGIS backend override |
| `DB_CONN_MAX_AGE` | PostgreSQL connection lifetime in seconds |
| `WEATHER_REQUEST_TIMEOUT` | Open-Meteo/Nominatim timeout |
| `SECURE_SSL_REDIRECT` | Enable HTTPS redirect in a proxy deployment |
| `HEALTH_MODEL_PATH` | Optional evaluated joblib classifier |

PostgreSQL uses `psycopg[binary]`. PostGIS is optional: the default SQLite
configuration does not import GIS fields or require GDAL.

## GitHub and Render

```powershell
git clone https://github.com/<owner>/<repo>.git
cd <repo>
copy .env.example .env
```

Render can deploy directly from `render.yaml`. Its build runs `build.sh`
(install, migrations and `collectstatic`) and Gunicorn serves
`config.wsgi:application`; `/healthz/` is the load-balancer probe. Set
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the Render hostname.

## Migrations, static files and ML

Run `python manage.py makemigrations` after model changes, then
`python manage.py migrate`. Production static files are collected into
`staticfiles/` and served by WhiteNoise. Run `python manage.py collectstatic
--no-input` to verify a deployment build.

No health-outcome dataset ships with this project. The default health signal
is a transparent planning baseline and makes no accuracy claim. With an
approved CSV containing the feature columns in `ml_models/train.py` and a
binary `target`, run:

```powershell
python -m ml_models.train labelled.csv --output-model health_model.joblib
```

The pipeline writes held-out accuracy/ROC-AUC metadata and requires
`HEALTH_MODEL_PATH` to activate the model. These metrics describe the supplied
dataset only, not clinical validity.

## Data classification and limitations

Open-Meteo and Nominatim responses are public external data. Coordinates
entered by a user are transient browser state unless an application extension
chooses to persist them; no personal identity is required. Thermal values are
screening calculations, not medical advice. WBGT uses an estimated globe
temperature when direct globe observations are unavailable, UTCI is an
approximation, and ward-level boundaries are not inferred. Forecast risk is
derived from each Open-Meteo daily row and is labelled `FORECAST` and
`CALCULATED`; it is not an alert guarantee.
