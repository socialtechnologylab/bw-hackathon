# Demand 1-day-ahead data

**Target:** `demand_mwh` — total Belgian electricity demand for the hour
ending at `timestamp`, in MWh.

**Cadence:** hourly, UTC. Timestamps are ISO-8601.

**Train range:** 2023-01-01 → 2025-01-01 (2 years).

**Test range:** 2025-01-01 → 2026-01-01 (12 months).
`y_test` lives on the scoring endpoint, not in this directory.

## Files

- `X_train.parquet` — features for the training window.
- `y_train.parquet` — `(timestamp, demand_mwh)`.
- `X_test.parquet` — features for the test window. **No `y_test`.**

## Feature columns (X_train.parquet, X_test.parquet)

| Column | Description | Units |
|---|---|---|
| `timestamp` | ISO-8601 hourly timestamp, UTC | — |
| `ghi_fcst` | Forecast global horizontal irradiance | W/m² |
| `t2m_fcst` | Forecast 2-metre air temperature | °C |
| `wind10m_fcst` | Forecast 10-metre wind speed | m/s |
| `cloud_cover_fcst` | Forecast cloud cover fraction | 0–1 |
| `hour` | Hour of day | 0–23 |
| `dow` | Day of week | 0–6 (Mon=0) |
| `month` | Month | 1–12 |

## Notes

- Data sources: ENTSO-E Transparency Platform for the demand series
  (target), NOAA GFS forecast cycles for the meteorological features.
  Features are real numerical-weather-prediction outputs, not ground
  truth — noisy proxies of the physical drivers.
- Demand has strong calendar structure (hour-of-day, day-of-week,
  holidays) on top of the weather signal. The features we ship don't
  encode holidays — that's deliberate.
- The relationship between features and target is not documented —
  discover it from the training data.
