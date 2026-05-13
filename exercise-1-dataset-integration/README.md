# Exercise 1 — Dataset integration

Your agent has to fetch a real public weather-forecast dataset, decode an
obscure binary format, and emit a clean, validated `parquet`. There is
no API SDK that hands you a DataFrame — you (your agent) have to do the
plumbing yourself.

You pass when `uv run pytest` is green.

## The contract

Produce `data/ecmwf_forecast.parquet` with **exactly** these columns, in
this order, with these dtypes:

| column | dtype | meaning |
|---|---|---|
| `valid_time` | `Utf8` (string) | ISO-8601 UTC, e.g. `"2025-03-01T03:00:00+00:00"` |
| `t2m_ecmwf_c` | `Float64` | 2-metre air temperature, **Celsius**, Belgian spatial mean |
| `wind10m_ecmwf_ms` | `Float64` | 10-metre wind speed `sqrt(u² + v²)`, **m/s**, Belgian spatial mean |

- **56 rows** total
- Sorted ascending by `valid_time`
- No nulls anywhere
- Belgian bounding box for the spatial mean: latitude `49.5..51.5`,
  longitude `2.5..6.5`

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
│   └── test_output.py    ← the validator
├── data/                 ← empty; you write the parquet here
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

Red until the parquet exists. Green once the schema, row count, range
checks, and spot-checks all pass. The spot-checks have ±0.5 °C and
±1.0 m/s tolerance, so honest spatial-averaging differences are fine.

## Rules

- Use the tarball above. Other GRIB sources (the ECMWF data portal, the
  AWS S3 mirror) throttle when 30 teams pull at once — don't go there.
- Do not modify the test file. Modify the producer code to match the
  contract, never the other way around.
- Your agent should be doing the work. You're building the harness
  around it — same operating posture as Exercise 2.
