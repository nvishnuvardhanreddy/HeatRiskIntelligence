"""ML seam for a validated health-risk model.

No health dataset ships with the MVP, so the default is an explicitly labelled
baseline. A trained joblib estimator can be enabled with HEALTH_MODEL_PATH
without changing API contracts.
"""
import os
from pathlib import Path

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    model_path = os.getenv("HEALTH_MODEL_PATH")
    if not model_path or not Path(model_path).is_file():
        return None
    try:
        import joblib
        _model = joblib.load(model_path)
    except Exception:
        _model = None
    return _model


def predict_health_risk(features: dict) -> dict:
    model = _load_model()
    if model is not None:
        try:
            ordered = [[features[key] for key in (
                "htsi", "temperature", "humidity", "wind_speed",
                "solar_radiation", "night_temperature", "vulnerability",
            )]]
            score = float(model.predict_proba(ordered)[0][1] * 100)
            return {"score": round(max(0, min(100, score)), 1), "label": "MODEL ESTIMATE", "model": "configured joblib"}
        except (KeyError, ValueError, AttributeError, IndexError):
            pass
    score = min(100, round(features["htsi"] * 0.9 + max(0, features["temperature"] - 34) * 1.2, 1))
    return {"score": score, "label": "MODEL ESTIMATE", "model": "transparent baseline (no validated dataset configured)"}

