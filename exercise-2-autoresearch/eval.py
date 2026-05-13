"""Autoresearch baseline for the BW hackathon — covers all 4 tasks.

Usage:
    uv run python eval.py <task-id>

Examples:
    uv run python eval.py solar-1d-ahead
    uv run python eval.py wind-2h-ahead

YOU MAY EDIT this file freely. For task-specific changes, edit the entry
for your task in TASK_CONFIG below — that keeps your hypothesis isolated
from the other tasks you might run later. The main() body below is the
shared submission + reporting pipeline; changing it affects every task,
so do it deliberately.

YOU MAY NOT EDIT:
- tasks/<id>/data/*.parquet (the data)
- .env (your team credentials)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import lightgbm as lgb
import polars as pl
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

# All the per-task knobs an agent might want to tune. Edit the entry for
# the task you're working on — leave the others alone unless you're
# applying a cross-task improvement deliberately. To add a feature only
# for one task, drop it into that task's `features` list; the others
# stay untouched.
TASK_CONFIG: dict[str, dict] = {
    "solar-1d-ahead": {
        "target": "solar_mwh",
        "features": [
            "ghi_fcst",
            "t2m_fcst",
            "wind10m_fcst",
            "cloud_cover_fcst",
            "hour",
            "dow",
            "month",
        ],
        "model_factory": lambda: lgb.LGBMRegressor(n_estimators=200, verbosity=-1),
    },
    "wind-2h-ahead": {
        "target": "wind_mwh",
        "features": [
            "ghi_fcst",
            "t2m_fcst",
            "wind10m_fcst",
            "cloud_cover_fcst",
            "hour",
            "dow",
            "month",
        ],
        "model_factory": lambda: lgb.LGBMRegressor(n_estimators=200, verbosity=-1),
    },
    "demand-1d-ahead-test": {
        "target": "demand_mwh",
        "features": [
            "ghi_fcst",
            "t2m_fcst",
            "wind10m_fcst",
            "cloud_cover_fcst",
            "hour",
            "dow",
            "month",
        ],
        "model_factory": lambda: lgb.LGBMRegressor(n_estimators=200, verbosity=-1),
    },
}


def main(task_id: str) -> None:
    if task_id not in TASK_CONFIG:
        raise SystemExit(
            f"unknown task '{task_id}'. valid: {sorted(TASK_CONFIG)}"
        )
    cfg = TASK_CONFIG[task_id]
    data_dir = ROOT / "tasks" / task_id / "data"

    X_train = pl.read_parquet(data_dir / "X_train.parquet")
    y_train = pl.read_parquet(data_dir / "y_train.parquet")
    X_test = pl.read_parquet(data_dir / "X_test.parquet")

    model = cfg["model_factory"]().fit(
        X_train[cfg["features"]].to_pandas(),
        y_train[cfg["target"]].to_pandas(),
    )
    preds = model.predict(X_test[cfg["features"]].to_pandas())

    resp = httpx.post(
        f"{os.environ['BW_ENDPOINT_URL']}/score",
        headers={"Authorization": f"Bearer {os.environ['BW_TEAM_TOKEN']}"},
        json={
            "task_id": task_id,
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
        f"[{task_id}] "
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

    importances = sorted(
        zip(cfg["features"], model.feature_importances_, strict=True),
        key=lambda x: -x[1],
    )
    print("\nTop feature importances:")
    for name, imp in importances[:5]:
        print(f"  {name:<24} {imp}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            f"usage: uv run python eval.py <task-id>  "
            f"(one of {sorted(TASK_CONFIG)})"
        )
    main(sys.argv[1])
