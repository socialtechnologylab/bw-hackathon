# Exercise 1 — Dataset integration

You want to use ECMWF weather forecasts as features for a forecasting
model. Only catch: ECMWF publishes them as **GRIB2** — a binary
scientific format that needs a native library to decode, has its own
coordinate conventions (0–360° longitude, latitude descending, units
in Kelvin), and was never designed to be ergonomic.

Your agent has to pull the data, decode it, and shape it into two
clean **zarr** stores:

- a **raw** spatial-mean series (one entry per forecast step), and
- a **model-ready** version (hourly, z-score normalised, ready to drop
  into a model's feature table).

When both stores pass the remote validator, you're done. The validator
runs 32 checks against the contract below and returns per-check
pass/fail — that's the binding sign-off.

## What you produce

Two zarr stores, both under `data/`. Each is an xarray Dataset with
`valid_time` as the coord/dim and named data_vars along it.

### 1. `data/ecmwf_forecast.zarr/` — the **raw** spatial-mean series

| element | spec |
|---|---|
| dim / coord | `valid_time`, dtype `datetime64[ns]`, length **56** |
| data var | `t2m_ecmwf_c`  — 2-metre air temperature, **Celsius**, Belgian spatial mean, dtype `float64` |
| data var | `wind10m_ecmwf_ms`  — 10-metre wind speed `sqrt(u² + v²)`, **m/s**, Belgian spatial mean, dtype `float64` |

- 56 entries (7 days × 8 three-hourly steps)
- `valid_time` strictly ascending, no NaNs in either variable
- Belgian bbox for the spatial mean: lat `49.5..51.5`, lon `2.5..6.5`

```python
import xarray as xr
ds = xr.open_zarr("data/ecmwf_forecast.zarr")
# ds.sel(valid_time="2025-03-01T03:00:00")["t2m_ecmwf_c"].item()
```

### 2. `data/ecmwf_features.zarr/` — the **model-ready** features

| element | spec |
|---|---|
| dim / coord | `valid_time`, dtype `datetime64[ns]`, length **166** |
| data var | `t2m_ecmwf_z`     — z-score normalised temperature, dtype `float64` |
| data var | `wind10m_ecmwf_z` — z-score normalised wind speed, dtype `float64` |

- 166 entries — derived from the raw store by:
  1. Resampling from 3-hourly to **hourly** by linear interpolation
     (`2025-03-01T00:00 .. 2025-03-07T21:00` inclusive)
  2. Z-score normalising each variable: `(x − mean) / std`
- Per-variable `mean ≈ 0` and `std ≈ 1`
- `valid_time` strictly ascending, exactly hourly cadence, no NaNs

## Where the data lives

[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
publishes the IFS HRES global forecast model as GRIB2. The slice you
need is pre-bundled in a release tarball so 30 teams can pull it in
parallel without rate-limit drama:

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

`valid_time = init_time + step_hours`. So the entry corresponding to
`20250301-00z-03h.grib2` has `valid_time = 2025-03-01T03:00:00`.

## How to know you're done

Two layers:

**Locally:** write your own tests. The brief above is the contract;
translate it into pytest cases under `tests/` and drive them red →
green as you build out the producer code. Useful test names to seed
your thinking:

- `test_raw_has_56_timesteps`
- `test_raw_data_vars_match_contract`
- `test_raw_t2m_plausible_for_belgian_march`
- `test_features_hourly_cadence`
- `test_features_each_var_has_zero_mean_and_unit_std`

We deliberately don't ship a validator — inferring a contract, writing
tests for it, then implementing against those tests is the discipline
we want you to practise.

**Remote:** once your local tests pass, **tar both stores into one
archive** and submit it for the binding pass/fail:

```bash
cp .env.example .env       # paste BW_TEAM_TOKEN from the card

# tar both zarr directories into one submission
tar -czf submission.tar.gz -C data ecmwf_forecast.zarr ecmwf_features.zarr

set -a; source .env; set +a
curl -X POST "$BW_ENDPOINT_URL/exercise-1/submit" \
  -H "Authorization: Bearer $BW_TEAM_TOKEN" \
  -F "submission=@submission.tar.gz"
```

You get JSON back:

```jsonc
{
  "passed": false,
  "passed_count": 28,
  "total": 32,
  "submission_id": "ab12cd34ef567890",
  "submitted_at": "2026-05-13T08:30:00+00:00",
  "results": [
    {"name": "raw.data_vars",     "passed": true,  "hint": ""},
    {"name": "features.t2m_ecmwf_z_unit_std", "passed": false,
     "hint": "t2m_ecmwf_z std isn't ≈ 1 — z-score divides by std, not min-max or N"},
    ...
  ]
}
```

Hints are deliberately terse — they tell you which check failed, never
the exact reference values. If you want to know exactly what your
output looks like, write a local test against your own expectations.

Submissions are rate-limited per team (about one every five seconds is
comfortable). Submit as many times as you like; each submission is
recorded.

## What you start with

```
.
├── README.md             ← this file
├── pyproject.toml        ← uv-managed; ships with polars + pytest only
├── .env.example          ← copy to .env and paste your BW_TEAM_TOKEN
├── tests/                ← empty — you write the tests
│   └── .gitkeep
├── data/                 ← empty; you write the zarr stores here
├── .claude/              ← permissions config (you can extend this)
└── .gitignore
```

You will need to add at least two Python dependencies: one for GRIB2
decoding (eccodes is a native library; cfgrib is the usual Python
wrapper) and one for writing zarr stores (xarray + zarr). Your agent
has to figure out the install dance.

## Rules

- Use the tarball above. Other GRIB sources (the ECMWF data portal,
  the AWS S3 mirror) throttle when 30 teams pull at once — don't go
  there.
- Use **linear interpolation** when resampling 3-hourly → hourly.
- Don't try to reverse-engineer the validator from its hint messages.
  Test against the contract; let the endpoint be the binding sign-off.
- Your agent should be doing the work. You're building the harness
  around it — same operating posture as Exercise 2.
