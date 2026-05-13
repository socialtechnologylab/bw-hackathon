# Program — `solar-1d-ahead`

## What you are doing

You are inside an autoresearch loop. Your job is to lower the MAE
this task posts to the scoring endpoint, repeatedly, autonomously, until
told to stop. The harness around you — the skills, hooks, slash commands
you write — is the artefact being graded.

## The loop

1. Read this file and `eval.py` (at the repo root).
2. Form a hypothesis about what would lower the MAE on
   **`solar-1d-ahead`** specifically (better features, model, hyperparams,
   lag features, calibration…).
3. Edit `TASK_CONFIG["solar-1d-ahead"]` in `eval.py`. Stay inside that
   entry — the shared submission pipeline and the other tasks' entries
   should not change unless you are deliberately applying a cross-task
   improvement.
4. Run `uv run python eval.py solar-1d-ahead`.
5. Read the printed MAE and the per-hour breakdown.
6. Log a one-line lesson in `tasks/solar-1d-ahead/experiments/log.md`
   (create the dir + file if missing).
7. Goto 2.

Target wall-clock per iteration: about 5 minutes. If a single iteration
takes much longer than that, your model is probably too heavy for the
budget — fall back to lighter learners.

## What the metric means

- `metric_value` = the **MAE in MWh** of your predictions vs the held-out
  ground truth, computed on the endpoint side. **Lower = better.** Aim
  to drive it as low as you can.
- `best_so_far` = the lowest `metric_value` your team has posted on this
  task today.
- The leaderboard ranks teams ascending by `best_so_far` per task.


## Per-sample feedback

The endpoint returns one row per prediction:

```
{ "timestamp": "...", "predicted": 12.4, "error": 0.3 }
```

`error = predicted - actual` (signed). Positive = overshoot. Negative =
undershoot. We never return `actual` — you have to learn from the error
shape, not the labels.

## What you may edit

- `eval.py` at the repo root — prefer editing only your task's entry in
  `TASK_CONFIG` so changes don't leak across tasks.
- Helper modules in this directory — create as many as you want, and
  import them from `eval.py`.

## What you may not edit

- `data/*.parquet` — the dataset.
- `.env` — your team credentials.

## What the data looks like

See `data/README.md`.

## What good looks like

A baseline LightGBM on the listed features gets MAE around 334 MWh on
real data — that's the number to beat. Tighter feature engineering, lag
features, or a calibrated ensemble can bring it well below 250 MWh.
