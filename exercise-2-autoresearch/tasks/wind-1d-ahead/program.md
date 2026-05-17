# Program — `wind-1d-ahead`

## What you are doing

You are inside an autoresearch loop. Your job is to lower the MAE
this task posts to the scoring endpoint, repeatedly, autonomously, until
told to stop. The harness around you — the skills, hooks, slash commands
you write — is the artefact being graded.

## The task

Day-ahead Belgium-aggregate **wind generation** (onshore + offshore
summed) in MWh, hourly. At 24h lead time, persistence stops working —
weather-forecast features have to carry the prediction.

## The loop

1. Read this file and `eval.py` (at the repo root).
2. Form a hypothesis about what would lower the MAE on
   **`wind-1d-ahead`** specifically (autoregressive lags, gust-aware
   features, persistence baselines, …).
3. Edit `TASK_CONFIG["wind-1d-ahead"]` in `eval.py`. Stay inside that
   entry — the shared submission pipeline and the other tasks' entries
   should not change unless you are deliberately applying a cross-task
   improvement.
4. Run `uv run python eval.py wind-1d-ahead`.
5. Read the printed MAE and the per-hour breakdown.
6. Log a one-line lesson in `tasks/wind-1d-ahead/experiments/log.md`
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
{ "timestamp": "...", "predicted": 1240.0, "error": 30.0 }
```

`error = predicted - actual` (signed). Positive = overshoot.

## What you may edit

- `eval.py` at the repo root — prefer editing only your task's entry in
  `TASK_CONFIG` so changes don't leak across tasks.
- Helper modules in this directory.

## What you may not edit

- `data/*.parquet` — the dataset.
- `.env` — your team identifier.

## What the data looks like

See `data/README.md`.

## What good looks like

Baseline LightGBM gets MAE around 25 MWh on real data. Wind is harder
to forecast than solar at this lead; reaching MAE under 15 MWh likely
needs autoregressive features and careful handling of the volatility
regime.
