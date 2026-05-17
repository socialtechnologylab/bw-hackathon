# Day-ahead wind energy (Belgium aggregate) — data

**Target column:** `wind_mwh`

**Cadence:** hourly, UTC. Timestamps are ISO-8601 with explicit `+00:00`.

**Train range:** 2023-01-01 → 2025-01-01
**Test range:**  2025-01-01 → 2026-01-01 (labels live on the scoring endpoint)

## Files

- `X_train.parquet` — features for the training window.
- `y_train.parquet` — `(timestamp, wind_mwh)`.
- `X_test.parquet` — features for the test window. **No `y_test`.**

## Feature columns

| Column | Description | Units |
|---|---|---|
| `timestamp` | ISO-8601 hourly timestamp, UTC | — |
| `ghi_fcst` | Forecast global horizontal irradiance (GFS `sdswrf`) | W/m² |
| `t2m_fcst` | Forecast 2-metre air temperature (GFS `tmp`) | °C |
| `wind10m_fcst` | Forecast 10-metre wind speed (GFS magnitude of u,v) | m/s |
| `cloud_cover_fcst` | Forecast total cloud cover (GFS `tcdc` / 100) | 0–1 |
| `hour` | Hour of day | 0–23 |
| `dow` | Day of week | 0–6 (Mon=0) |
| `month` | Month | 1–12 |

## Provenance

- Targets: ENTSO-E B19 (Wind Onshore) + B18 (Wind Offshore) summed, Belgium
- Features: GFS 0.25° from the AWS public S3 mirror (`s3://noaa-gfs-bdp-pds/`),
  init cycles 00 / 06 / 12 / 18 UTC, area-mean over Belgium bbox
  (lat 49.5–51.5, lon 2.5–6.5).
- Forecast alignment: latest cycle initialised ≥ 24 hours before t.

## Quirks

- 24 of 26302 hours dropped due to missing data (0.09%).
- Timestamps with no aligned GFS cycle are dropped silently.

## Baseline

Observed baseline MAE: **486.406 MWh** from
`LGBMRegressor(n_estimators=200, verbosity=-1)` on the listed feature
columns. That's the number to beat. Measured 2026-05-17.

Source: `bw-hackathon-data/scripts/calibrate.py`.
