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
  longitude `2.5..6.5` (matches Exercise 2 — same Belgium)

## The data

[ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)
publishes the IFS HRES global forecast model output as **GRIB2** files,
mirrored on a public AWS bucket (no auth, no key, no rate limits to
worry about for what you need).

Pull the **00 UTC initialisation** for each day in
**2025-03-01 .. 2025-03-07 (inclusive)**, and from each one extract
forecast **steps 0, 3, 6, 9, 12, 15, 18, 21** hours. Three surface
variables per step: `2t` (2-metre temperature), `10u` and `10v` (10-metre
wind components). That gives 7 days × 8 steps = **56 rows**.

`valid_time = initialisation_time + step_hours`. So the row for
`(init=2025-03-01T00Z, step=3h)` has `valid_time = 2025-03-01T03:00:00+00:00`.

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

- The dataset must come from ECMWF Open Data. Any source/route into that
  data is acceptable (raw HTTP byte-range, an SDK, etc.). Other weather
  datasets are out of scope for this exercise.
- Do not modify the test file. Modify the producer code to match the
  contract, never the other way around.
- Your agent should be doing the work. You're building the harness
  around it — same operating posture as Exercise 2.
