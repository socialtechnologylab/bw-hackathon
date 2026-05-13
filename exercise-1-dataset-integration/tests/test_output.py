"""Validator for Exercise 1.

Green = your agent fetched, decoded, and reshaped the ECMWF forecast
correctly. Red = something's off — read the assertion message.

Reference sample values were captured by the trainer's reference solver
(same source, same window, same bbox). Tolerances are loose enough to
allow legitimate variation in spatial averaging (bilinear vs nearest,
inclusive vs exclusive bbox edges) but tight enough that "fetched the
wrong day" or "didn't filter to Belgium" will fail.
"""

from __future__ import annotations

import math
from pathlib import Path

import polars as pl
import pytest

PARQUET = (
    Path(__file__).resolve().parent.parent / "data" / "ecmwf_forecast.parquet"
)

EXPECTED_COLUMNS = ("valid_time", "t2m_ecmwf_c", "wind10m_ecmwf_ms")
EXPECTED_DTYPES = {
    "valid_time": pl.Utf8,
    "t2m_ecmwf_c": pl.Float64,
    "wind10m_ecmwf_ms": pl.Float64,
}
EXPECTED_ROWS = 56

# (valid_time): (t2m_ecmwf_c, wind10m_ecmwf_ms)  — within tolerances below
REFERENCE_SAMPLES: dict[str, tuple[float, float]] = {
    "2025-03-01T00:00:00+00:00": (1.370, 2.636),
    "2025-03-03T06:00:00+00:00": (-1.853, 0.872),
    "2025-03-05T15:00:00+00:00": (13.786, 1.872),
    "2025-03-07T21:00:00+00:00": (7.836, 2.902),
}
T2M_TOL_C = 0.5
WIND_TOL_MS = 1.0


@pytest.fixture(scope="module")
def df() -> pl.DataFrame:
    assert PARQUET.exists(), (
        f"missing {PARQUET.relative_to(Path.cwd()) if PARQUET.is_relative_to(Path.cwd()) else PARQUET}"
        " — produce the parquet before running the validator"
    )
    return pl.read_parquet(PARQUET)


def test_schema_columns(df: pl.DataFrame) -> None:
    assert tuple(df.columns) == EXPECTED_COLUMNS, (
        f"columns must be exactly {EXPECTED_COLUMNS} in this order; got {tuple(df.columns)}"
    )


def test_schema_dtypes(df: pl.DataFrame) -> None:
    actual = {c: df.schema[c] for c in df.columns}
    assert actual == EXPECTED_DTYPES, (
        f"dtypes must be {EXPECTED_DTYPES}; got {actual}"
    )


def test_row_count(df: pl.DataFrame) -> None:
    assert df.height == EXPECTED_ROWS, (
        f"expected {EXPECTED_ROWS} rows (7 days × 8 three-hourly steps), got {df.height}"
    )


def test_sorted_ascending(df: pl.DataFrame) -> None:
    assert df["valid_time"].is_sorted(), "rows must be sorted by valid_time ascending"


def test_no_nulls(df: pl.DataFrame) -> None:
    for col in df.columns:
        nulls = df[col].null_count()
        assert nulls == 0, f"{col} has {nulls} null(s); expected none"


def test_t2m_envelope(df: pl.DataFrame) -> None:
    lo, hi = df["t2m_ecmwf_c"].min(), df["t2m_ecmwf_c"].max()
    assert -15.0 < lo, f"t2m_ecmwf_c min {lo} is implausibly cold for Belgium in March"
    assert hi < 25.0, f"t2m_ecmwf_c max {hi} is implausibly warm for Belgium in March"


def test_wind_envelope(df: pl.DataFrame) -> None:
    lo, hi = df["wind10m_ecmwf_ms"].min(), df["wind10m_ecmwf_ms"].max()
    assert lo >= 0.0, f"wind10m_ecmwf_ms min {lo} < 0 (speed cannot be negative)"
    assert hi < 40.0, f"wind10m_ecmwf_ms max {hi} ≥ 40 m/s — extreme storm or unit bug"


@pytest.mark.parametrize("ts", list(REFERENCE_SAMPLES))
def test_sample_row_within_tolerance(df: pl.DataFrame, ts: str) -> None:
    expected_t, expected_w = REFERENCE_SAMPLES[ts]
    row = df.filter(pl.col("valid_time") == ts)
    assert row.height == 1, f"missing or duplicated row for valid_time={ts!r}"
    actual_t = row["t2m_ecmwf_c"][0]
    actual_w = row["wind10m_ecmwf_ms"][0]
    assert math.isclose(actual_t, expected_t, abs_tol=T2M_TOL_C), (
        f"t2m_ecmwf_c at {ts}: expected ≈ {expected_t:+.3f} °C "
        f"(±{T2M_TOL_C}), got {actual_t:+.3f}"
    )
    assert math.isclose(actual_w, expected_w, abs_tol=WIND_TOL_MS), (
        f"wind10m_ecmwf_ms at {ts}: expected ≈ {expected_w:.3f} m/s "
        f"(±{WIND_TOL_MS}), got {actual_w:.3f}"
    )
