"""Optional, reproducible training entry point for a labelled CSV dataset.

The project ships no health-outcome dataset. Run this only with an approved
dataset containing the documented feature columns and a binary ``target``.
Metrics are written only after an explicit hold-out evaluation.
"""
import argparse
import json
from datetime import date
from pathlib import Path

FEATURES = [
    "htsi", "temperature", "humidity", "wind_speed",
    "solar_radiation", "night_temperature", "vulnerability",
]


def train(input_csv: str, output_model: str, output_metadata: str) -> dict:
    import joblib
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    data = pd.read_csv(input_csv)
    missing = [column for column in FEATURES + ["target"] if column not in data]
    if missing:
        raise ValueError("Dataset is missing columns: " + ", ".join(missing))
    train_x, test_x, train_y, test_y = train_test_split(
        data[FEATURES], data["target"], test_size=0.2, random_state=42, stratify=data["target"]
    )
    model = LogisticRegression(max_iter=1000).fit(train_x, train_y)
    probability = model.predict_proba(test_x)[:, 1]
    metadata = {
        "version": "logistic-regression-1.0",
        "training_date": date.today().isoformat(),
        "features": FEATURES,
        "metrics": {
            "accuracy": round(float(accuracy_score(test_y, probability >= 0.5)), 4),
            "roc_auc": round(float(roc_auc_score(test_y, probability)), 4),
            "test_rows": int(len(test_y)),
        },
        "evaluation_status": "held-out test split",
        "disclaimer": "Metrics describe this dataset and split; they are not a clinical validation.",
    }
    joblib.dump(model, output_model)
    Path(output_metadata).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the optional Ground Zero risk model.")
    parser.add_argument("input_csv")
    parser.add_argument("--output-model", default="health_model.joblib")
    parser.add_argument("--output-metadata", default="health_model_metadata.json")
    args = parser.parse_args()
    print(json.dumps(train(args.input_csv, args.output_model, args.output_metadata), indent=2))
