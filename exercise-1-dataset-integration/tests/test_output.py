"""Validator for Exercise 1.

Green = your agent fetched, decoded, reshaped, and prepped the ECMWF
forecast correctly. Red = something's off — read the assertion message.

Two parquets are validated:
1. `data/ecmwf_forecast.parquet` — raw 3-hourly spatial means in
   °C / m/s, 56 rows. The decoding output.
2. `data/ecmwf_features.parquet` — hourly (linearly interpolated from
   the 3-hourly grid), z-score normalised, 166 rows. The model-ready
   output.

Reference sample values were captured by the trainer's reference solver.
Tolerances are loose enough to allow legitimate variation in spatial
averaging (bilinear vs nearest, inclusive vs exclusive bbox edges) but
tight enough that "fetched the wrong day" or "didn't filter to Belgium"
will fail immediately.
"""

from __future__ import annotations

import math
from pathlib import Path

import polars as pl
import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_PARQUET = DATA_DIR / "ecmwf_forecast.parquet"
FEATURES_PARQUET = DATA_DIR / "ecmwf_features.parquet"


# ── Raw 3-hourly contract ─────────────────────────────────────────────────────

RAW_COLUMNS = ("valid_time", "t2m_ecmwf_c", "wind10m_ecmwf_ms")
RAW_DTYPES = {
    "valid_time": pl.Utf8,
    "t2m_ecmwf_c": pl.Float64,
    "wind10m_ecmwf_ms": pl.Float64,
}
RAW_EXPECTED_ROWS = 56
RAW_REFERENCE_SAMPLES: dict[str, tuple[float, float]] = {
    "2025-03-01T00:00:00+00:00": (1.370, 2.636),
    "2025-03-03T06:00:00+00:00": (-1.853, 0.872),
    "2025-03-05T15:00:00+00:00": (13.786, 1.872),
    "2025-03-07T21:00:00+00:00": (7.836, 2.902),
}
RAW_T2M_TOL_C = 0.5
RAW_WIND_TOL_MS = 1.0


# ── Features (model-ready) contract ───────────────────────────────────────────

FEATURES_COLUMNS = ("valid_time", "t2m_ecmwf_z", "wind10m_ecmwf_z")
FEATURES_DTYPES = {
    "valid_time": pl.Utf8,
    "t2m_ecmwf_z": pl.Float64,
    "wind10m_ecmwf_z": pl.Float64,
}
FEATURES_EXPECTED_ROWS = 166  # 03-01T00 .. 03-07T21 hourly inclusive
FEATURES_REFERENCE_SAMPLES: dict[str, tuple[float, float]] = {
    "2025-03-01T00:00:00+00:00": (-0.8987, 0.3961),
    "2025-03-03T07:00:00+00:00": (-1.1939, -1.4972),
    "2025-03-05T14:00:00+00:00": (1.8067, -0.2830),
    "2025-03-07T21:00:00+00:00": (0.5514, 0.6679),
}
FEATURES_Z_TOL = 0.15  # generous — different interpolation strategies vary
FEATURES_MEAN_TOL = 1e-9  # mean must be ≈ 0 to float precision
# Loose enough to accept both polars (ddof=1, std=1.000) and sklearn
# (ddof=0, polars-measured std≈1.003 for N=166) z-score conventions.
FEATURES_STD_TOL = 1e-2


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def raw() -> pl.DataFrame:
    assert RAW_PARQUET.exists(), (
        f"missing data/ecmwf_forecast.parquet — produce the raw parquet before running the validator"
    )
    return pl.read_parquet(RAW_PARQUET)


@pytest.fixture(scope="module")
def features() -> pl.DataFrame:
    assert FEATURES_PARQUET.exists(), (
        f"missing data/ecmwf_features.parquet — produce the model-ready parquet before running the validator"
    )
    return pl.read_parquet(FEATURES_PARQUET)


# ── Raw parquet tests ─────────────────────────────────────────────────────────


def test_raw_schema_columns(raw: pl.DataFrame) -> None:
    assert tuple(raw.columns) == RAW_COLUMNS, (
        f"raw columns must be exactly {RAW_COLUMNS} in this order; got {tuple(raw.columns)}"
    )


def test_raw_schema_dtypes(raw: pl.DataFrame) -> None:
    actual = {c: raw.schema[c] for c in raw.columns}
    assert actual == RAW_DTYPES, f"raw dtypes must be {RAW_DTYPES}; got {actual}"


def test_raw_row_count(raw: pl.DataFrame) -> None:
    assert raw.height == RAW_EXPECTED_ROWS, (
        f"raw expected {RAW_EXPECTED_ROWS} rows (7 days × 8 three-hourly steps), got {raw.height}"
    )


def test_raw_sorted_ascending(raw: pl.DataFrame) -> None:
    assert raw["valid_time"].is_sorted(), "raw rows must be sorted by valid_time ascending"


def test_raw_no_nulls(raw: pl.DataFrame) -> None:
    for col in raw.columns:
        nulls = raw[col].null_count()
        assert nulls == 0, f"raw {col} has {nulls} null(s); expected none"


def test_raw_t2m_envelope(raw: pl.DataFrame) -> None:
    lo, hi = raw["t2m_ecmwf_c"].min(), raw["t2m_ecmwf_c"].max()
    assert -15.0 < lo, f"raw t2m_ecmwf_c min {lo} is implausibly cold for Belgium in March"
    assert hi < 25.0, f"raw t2m_ecmwf_c max {hi} is implausibly warm for Belgium in March"


def test_raw_wind_envelope(raw: pl.DataFrame) -> None:
    lo, hi = raw["wind10m_ecmwf_ms"].min(), raw["wind10m_ecmwf_ms"].max()
    assert lo >= 0.0, f"raw wind10m_ecmwf_ms min {lo} < 0 (speed cannot be negative)"
    assert hi < 40.0, f"raw wind10m_ecmwf_ms max {hi} ≥ 40 m/s — extreme storm or unit bug"


@pytest.mark.parametrize("ts", list(RAW_REFERENCE_SAMPLES))
def test_raw_sample_row_within_tolerance(raw: pl.DataFrame, ts: str) -> None:
    expected_t, expected_w = RAW_REFERENCE_SAMPLES[ts]
    row = raw.filter(pl.col("valid_time") == ts)
    assert row.height == 1, f"raw missing or duplicated row for valid_time={ts!r}"
    actual_t = row["t2m_ecmwf_c"][0]
    actual_w = row["wind10m_ecmwf_ms"][0]
    assert math.isclose(actual_t, expected_t, abs_tol=RAW_T2M_TOL_C), (
        f"raw t2m_ecmwf_c at {ts}: expected ≈ {expected_t:+.3f} °C "
        f"(±{RAW_T2M_TOL_C}), got {actual_t:+.3f}"
    )
    assert math.isclose(actual_w, expected_w, abs_tol=RAW_WIND_TOL_MS), (
        f"raw wind10m_ecmwf_ms at {ts}: expected ≈ {expected_w:.3f} m/s "
        f"(±{RAW_WIND_TOL_MS}), got {actual_w:.3f}"
    )


# ── Features parquet tests ────────────────────────────────────────────────────


def test_features_schema_columns(features: pl.DataFrame) -> None:
    assert tuple(features.columns) == FEATURES_COLUMNS, (
        f"features columns must be exactly {FEATURES_COLUMNS} in this order; got {tuple(features.columns)}"
    )


def test_features_schema_dtypes(features: pl.DataFrame) -> None:
    actual = {c: features.schema[c] for c in features.columns}
    assert actual == FEATURES_DTYPES, f"features dtypes must be {FEATURES_DTYPES}; got {actual}"


def test_features_row_count(features: pl.DataFrame) -> None:
    assert features.height == FEATURES_EXPECTED_ROWS, (
        f"features expected {FEATURES_EXPECTED_ROWS} rows "
        f"(hourly from 2025-03-01T00:00 to 2025-03-07T21:00 inclusive), got {features.height}"
    )


def test_features_sorted_ascending(features: pl.DataFrame) -> None:
    assert features["valid_time"].is_sorted(), "features rows must be sorted by valid_time ascending"


def test_features_no_nulls(features: pl.DataFrame) -> None:
    for col in features.columns:
        nulls = features[col].null_count()
        assert nulls == 0, f"features {col} has {nulls} null(s); expected none"


def test_features_hourly_cadence(features: pl.DataFrame) -> None:
    ts = features["valid_time"].str.to_datetime(format="%Y-%m-%dT%H:%M:%S%z")
    diffs = ts.diff().drop_nulls()
    unique_diffs = sorted(set(diffs.dt.total_seconds().to_list()))
    assert unique_diffs == [3600.0], (
        f"features must be at exactly hourly cadence; "
        f"observed inter-row deltas (seconds): {unique_diffs}"
    )


@pytest.mark.parametrize("col", ("t2m_ecmwf_z", "wind10m_ecmwf_z"))
def test_features_zero_mean(features: pl.DataFrame, col: str) -> None:
    m = features[col].mean()
    assert abs(m) < FEATURES_MEAN_TOL, (
        f"features {col} mean must be ≈ 0 (within {FEATURES_MEAN_TOL}); got {m:+.3e}. "
        f"Did you forget to subtract the mean before scaling?"
    )


@pytest.mark.parametrize("col", ("t2m_ecmwf_z", "wind10m_ecmwf_z"))
def test_features_unit_std(features: pl.DataFrame, col: str) -> None:
    s = features[col].std()
    assert math.isclose(s, 1.0, abs_tol=FEATURES_STD_TOL), (
        f"features {col} std must be ≈ 1 (within {FEATURES_STD_TOL}); got {s:.6f}. "
        f"Did you scale by std (z-score), or only mean-centre, or min-max?"
    )


@pytest.mark.parametrize("ts", list(FEATURES_REFERENCE_SAMPLES))
def test_features_sample_row_within_tolerance(features: pl.DataFrame, ts: str) -> None:
    expected_t, expected_w = FEATURES_REFERENCE_SAMPLES[ts]
    row = features.filter(pl.col("valid_time") == ts)
    assert row.height == 1, f"features missing or duplicated row for valid_time={ts!r}"
    actual_t = row["t2m_ecmwf_z"][0]
    actual_w = row["wind10m_ecmwf_z"][0]
    assert math.isclose(actual_t, expected_t, abs_tol=FEATURES_Z_TOL), (
        f"features t2m_ecmwf_z at {ts}: expected ≈ {expected_t:+.4f} "
        f"(±{FEATURES_Z_TOL}), got {actual_t:+.4f}. "
        f"(Did you use linear interpolation between the 3-hourly raw points?)"
    )
    assert math.isclose(actual_w, expected_w, abs_tol=FEATURES_Z_TOL), (
        f"features wind10m_ecmwf_z at {ts}: expected ≈ {expected_w:+.4f} "
        f"(±{FEATURES_Z_TOL}), got {actual_w:+.4f}"
    )
