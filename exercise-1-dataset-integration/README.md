# Exercise 1 — Dataset integration

Your agent has to fetch a real public weather-forecast dataset, decode
an obscure binary format, reshape it into a clean parquet, and **prep
it for a prediction model** — resampled to the model's cadence and
z-score normalised.

You pass when `uv run pytest` is green.

## What you produce

Two parquets, both under `data/`:

### 1. `data/ecmwf_forecast.parquet` — the **raw** spatial-mean series

| column | dtype | meaning |
|---|---|---|
| `valid_time` | `Utf8` (string) | ISO-8601 UTC, e.g. `"2025-03-01T03:00:00+00:00"` |
| `t2m_ecmwf_c` | `Float64` | 2-metre air temperature, **Celsius**, Belgian spatial mean |
| `wind10m_ecmwf_ms` | `Float64` | 10-metre wind speed `sqrt(u² + v²)`, **m/s**, Belgian spatial mean |

- **56 rows** (7 days × 8 three-hourly steps)
- Sorted ascending by `valid_time`
- No nulls
- Belgian bbox for the spatial mean: lat `49.5..51.5`, lon `2.5..6.5`

### 2. `data/ecmwf_features.parquet` — the **model-ready** features

| column | dtype | meaning |
|---|---|---|
| `valid_time` | `Utf8` (string) | ISO-8601 UTC, hourly |
| `t2m_ecmwf_z` | `Float64` | z-score normalised temperature |
| `wind10m_ecmwf_z` | `Float64` | z-score normalised wind speed |

- **166 rows** — derived from the raw parquet by:
  1. Resampling from 3-hourly to **hourly** by linear interpolation
     (`2025-03-01T00:00 .. 2025-03-07T21:00` inclusive)
  2. Z-score normalising each numeric column: `(x − mean) / std`
- Per-column `mean ≈ 0` and `std ≈ 1`
- Sorted ascending, no nulls, exactly hourly cadence

## The data

[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
publishes the IFS HRES global forecast model as **GRIB2** files. The
slice you need is pre-bundled in a release tarball so 30 teams can pull
it in parallel without rate-limit drama:

> **URL**: `https://github.com/socialtechnologylab/bw-hackathon/releases/download/ecmwf-data-v1/ecmwf-grib2-belgium-2025-03-01-to-07.tar.gz`
> **SHA-256**: `6ce4a05be9301cc0bf0af3a286c57c40f5e21e735c8c6d8006f765c25d8e7d5e`
> **Size**: ~126 MiB

The tarball expands to a single directory with **56 `.grib2` files**, one
per `(init_date, forecast_step)`:

- Init time: **00 UTC** on each day in **2025-03-01..2025-03-07** (inclusive)
- Forecast steps: **0, 3, 6, 9, 12, 15, 18, 21 hours**
- File naming: `<YYYYMMDD>-00z-<SS>h.grib2` (e.g. `20250301-00z-12h.grib2`)
- Each file contains exactly **three surface messages**: `2t` (2-metre
  temperature, Kelvin), `10u` and `10v` (10-metre wind components, m/s)

`valid_time = init_time + step_hours`. So the row for `20250301-00z-03h.grib2`
has `valid_time = 2025-03-01T03:00:00+00:00`.

## What you start with

```
.
├── README.md             ← this file
├── pyproject.toml        ← uv-managed; ships with polars + pytest only
├── tests/
│   └── test_output.py    ← the validator (25 tests)
├── data/                 ← empty; you write both parquets here
└── .gitignore
```

You will need to add at least one Python dependency for GRIB2 decoding.
GRIB2 needs a native library (eccodes) backing the Python bindings;
your agent has to deal with that.

## Running the tests

```bash
uv sync
uv run pytest -v
```

Red until both parquets exist with the right shape.

11 tests cover the raw parquet (schema, count, sort, nulls, envelope,
sample-row spot-checks ±0.5 °C / ±1.0 m/s).

14 tests cover the features parquet (schema, count, sort, nulls, hourly
cadence, per-column zero mean to float precision, per-column unit std
within 1%, sample-row spot-checks ±0.15).

The std tolerance accommodates both `ddof=1` (polars / numpy
`ddof=1`) and `ddof=0` (sklearn `StandardScaler`) conventions.

## Rules

- Use the tarball above. Other GRIB sources (the ECMWF data portal, the
  AWS S3 mirror) throttle when 30 teams pull at once — don't go there.
- Use **linear interpolation** when resampling 3-hourly → hourly.
  Other methods (cubic, spline) shift the sample rows enough to bust
  the tolerance.
- Do not modify the test file. Modify the producer code to match the
  contract, never the other way around.
- Your agent should be doing the work. You're building the harness
  around it — same operating posture as Exercise 2.
