"""Autoresearch baseline for wind-1d-ahead.

Usage (from this directory):
    uv run python eval.py

Or from the repo root:
    uv run python tasks/wind-1d-ahead/eval.py

YOU MAY EDIT this file freely — it's the entire experiment surface for
this task. Add features, swap models, write transforms, build ensembles,
anything that fits the iteration budget.

YOU MAY NOT EDIT:
- data/*.parquet (the data)
- ../../.env  (your team identifier)
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import polars as pl
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression

HERE = Path(__file__).resolve().parent          # tasks/wind-1d-ahead/
REPO_ROOT = HERE.parent.parent
DATA_DIR = HERE / "data"

load_dotenv(REPO_ROOT / ".env")

TASK_ID = "wind-1d-ahead"
TARGET = "wind_mwh"
FEATURES = [
    "ghi_fcst",
    "t2m_fcst",
    "wind10m_fcst",
    "cloud_cover_fcst",
]


def make_model():
    return LinearRegression()


def main() -> None:
    X_train = pl.read_parquet(DATA_DIR / "X_train.parquet")
    y_train = pl.read_parquet(DATA_DIR / "y_train.parquet")
    X_test = pl.read_parquet(DATA_DIR / "X_test.parquet")

    model = make_model().fit(
        X_train[FEATURES].to_pandas(),
        y_train[TARGET].to_pandas(),
    )
    preds = model.predict(X_test[FEATURES].to_pandas())

    resp = httpx.post(
        f"{os.environ.get('BW_ENDPOINT_URL', 'https://bw.stl.dev')}/score",
        json={
            "task_id": TASK_ID,
            "team_id": os.environ["BW_TEAM_ID"],
            "predictions": [
                {"timestamp": str(ts), "value": float(v)}
                for ts, v in zip(X_test["timestamp"], preds)
            ],
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    result = resp.json()

    print(
        f"[{TASK_ID}] "
        f"MAE={result['metric_value']:.3f}  "
        f"best_so_far={result['best_so_far']:.3f}  (lower is better)"
    )

    per_sample = pl.DataFrame(result["per_sample"]).with_columns(
        pl.col("timestamp")
        .str.to_datetime(format="%Y-%m-%dT%H:%M:%S%z")
        .dt.hour()
        .alias("hour")
    )
    mean_error = per_sample["error"].mean()
    direction = "overpredicting" if mean_error > 0 else "underpredicting"
    print(f"\nglobal mean_error={mean_error:+.3f} ({direction})")

    by_hour = (
        per_sample.group_by("hour")
        .agg(
            pl.col("error").mean().alias("mean_error"),
            pl.col("error").abs().mean().alias("mae"),
        )
        .sort("hour")
    )
    print("\nBy hour of day:")
    print(by_hour)

    coefs = sorted(
        zip(FEATURES, model.coef_, strict=True),
        key=lambda x: -abs(x[1]),
    )
    print("\nCoefficients (by magnitude):")
    for name, c in coefs:
        print(f"  {name:<24} {c:+.4f}")


if __name__ == "__main__":
    main()
