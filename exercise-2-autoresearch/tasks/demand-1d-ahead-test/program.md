# Program — `demand-1d-ahead-test`

## What you are doing

You are inside an autoresearch loop. Your job is to lower the MAE
this task posts to the scoring endpoint, repeatedly, autonomously, until
told to stop. The harness around you — the skills, hooks, slash commands
you write — is the artefact being graded.

## The task

Day-ahead **Belgium total electricity demand** (ENTSO-E Actual Total
Load), in MWh, hourly. The signal has a twin-peak diurnal shape, strong
weekly seasonality (weekdays vs weekends), and big day-of-week and
holiday effects. The weather features matter for heating/cooling load.

## The loop

1. Read this file and `eval.py` (at the repo root).
2. Form a hypothesis about what would lower the MAE on
   **`demand-1d-ahead-test`** specifically (calendar features beyond
   hour/dow/month, holiday indicators, lagged loads, residual modelling
   on temperature, …).
3. Edit `TASK_CONFIG["demand-1d-ahead-test"]` in `eval.py`. Stay inside that
   entry — the shared submission pipeline and the other tasks' entries
   should not change unless you are deliberately applying a cross-task
   improvement.
4. Run `uv run python eval.py demand-1d-ahead-test`.
5. Read the printed MAE and the per-hour breakdown.
6. Log a one-line lesson in `tasks/demand-1d-ahead-test/experiments/log.md`
   (create the dir + file if missing).
7. Goto 2.

Target wall-clock per iteration: about 5 minutes.

## What the metric means

- `metric_value` = the **MAE in MWh** of your predictions vs the held-out
  ground truth, computed on the endpoint side. **Lower = better.** Aim
  to drive it as low as you can.
- `best_so_far` = the lowest `metric_value` your team has posted on this
  task today.
- The leaderboard ranks teams ascending by `best_so_far` per task.


## Per-sample feedback

```
{ "timestamp": "...", "predicted": 9450.0, "error": -120.0 }
```

`error = predicted - actual` (signed). Negative = undershoot.

## What you may edit

- `eval.py` at the repo root — prefer editing only your task's entry in
  `TASK_CONFIG` so changes don't leak across tasks.
- Helper modules in this directory.

## What you may not edit

- `data/*.parquet` — the dataset.
- `.env` — your team identifier.

## What the data looks like

See `data/README.md`. Note: the shipped feature set does NOT include
`is_holiday` — the Belgian official holiday calendar is the obvious
external feature to fetch and join in yourself (see `python-holidays`).
That's a deliberate exercise hook.

## What good looks like

Baseline LightGBM gets MAE around 385 MWh on real data. Adding holiday
indicators alone typically takes a chunk off that. Sub-200 MWh likely
needs careful interaction modelling (hour × dow, weather × hour) and
either lagged-load features or a proper time-series model.
