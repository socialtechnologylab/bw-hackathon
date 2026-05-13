# Exercise 1 — Dataset integration

Your agent has to fetch a real public weather-forecast dataset, decode
an obscure binary format, reshape it into a clean parquet, prep a
second model-ready parquet, and prove correctness by submitting both
files to a remote validator.

**There is no local validator.** You don't `uv run pytest` against a
file we ship you. You read the contract below, write **your own tests**
in `tests/` to enforce it, drive them red → green (TDD), and only then
POST to the endpoint for the binding pass/fail.

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

## TDD posture — write your own tests

The brief above is the contract. Translate it into pytest cases under
`tests/` **before** you write any decode/transform code. A typical
sketch:

- `test_raw_schema_matches_contract`
- `test_raw_has_56_rows`
- `test_raw_t2m_plausible_for_belgian_march`
- `test_features_hourly_cadence`
- `test_features_mean_is_zero_and_std_is_one`
- ...

Run them locally with `uv run pytest`. They should be red until you've
implemented `fetch.py` / `transform.py` / whatever you decide to call
your producer code. Drive them to green. Then — and only then — submit.

We deliberately don't ship a validator. The discipline of inferring a
contract → writing tests → driving to green is part of what you're
learning today.

## The submission endpoint

First, set up your credentials (one-time):

```bash
cp .env.example .env
# edit .env — paste BW_TEAM_TOKEN from the card you were handed
```

Once your local tests pass, send the two parquets to the validator
(loading credentials from `.env` via your tool of choice — `set -a; source .env; set +a`,
`uv run --env-file=.env`, `direnv`, or just `python-dotenv` inside a
script):

```bash
set -a; source .env; set +a
curl -X POST "$BW_ENDPOINT_URL/exercise-1/submit" \
  -H "Authorization: Bearer $BW_TEAM_TOKEN" \
  -F "forecast=@data/ecmwf_forecast.parquet" \
  -F "features=@data/ecmwf_features.parquet"
```

The response is JSON:

```jsonc
{
  "passed": false,
  "passed_count": 23,
  "total": 27,
  "submission_id": "ab12cd34ef567890",
  "submitted_at": "2026-05-13T08:30:00+00:00",
  "results": [
    {"name": "raw.schema_columns",      "passed": true,  "hint": ""},
    {"name": "features.t2m_ecmwf_z_unit_std", "passed": false,
     "hint": "t2m_ecmwf_z std isn't ≈ 1 — z-score divides by std, not min-max or N"},
    ...
  ]
}
```

Hints are deliberately terse — they tell you which category of check
failed, never the exact reference values. If you want to know exactly
what your output looks like, write a local test against your own
expectations.

Submissions are rate-limited per team (shared limiter with `/score` —
about one submission every five seconds is comfortable). You can
submit as many times as you like; the endpoint records each
submission's pass/fail.

## What you start with

```
.
├── README.md             ← this file
├── pyproject.toml        ← uv-managed; ships with polars + pytest only
├── .env.example          ← copy to .env and paste your BW_TEAM_TOKEN
├── tests/                ← empty — you write the tests
│   └── .gitkeep
├── data/                 ← empty; you write the parquets here
├── .claude/              ← permissions config (you can extend this)
└── .gitignore
```

You will need to add at least one Python dependency for GRIB2 decoding.
GRIB2 needs a native library (eccodes) backing the Python bindings;
your agent has to deal with that.

## Rules

- Use the tarball above. Other GRIB sources (the ECMWF data portal, the
  AWS S3 mirror) throttle when 30 teams pull at once — don't go there.
- Use **linear interpolation** when resampling 3-hourly → hourly.
- Don't try to reverse-engineer the validator from its hint messages.
  Test against the contract; let the endpoint be the binding sign-off.
- Your agent should be doing the work. You're building the harness
  around it — same operating posture as Exercise 2.
