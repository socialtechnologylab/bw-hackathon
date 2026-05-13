# Conventions

- Python ≥ 3.11. Package management: `uv` only. No `pip`.
- Data: `polars` for reading parquets, `pandas` only at the LightGBM
  interface boundary (`.to_pandas()`).
- ML default: `lightgbm` baseline. Anything heavier (XGBoost, sklearn
  ensembles, etc.) is fine if it fits the 5-minute per-iteration budget.
- Editing scope: the shared `eval.py` lives at the repo root with one
  `TASK_CONFIG["<task-id>"]` entry per task. Edit only the entry for
  the task you're working on. Don't touch `tasks/*/data/*.parquet` or
  `.env`. The shared pipeline below `TASK_CONFIG` is fair game for
  deliberate cross-task improvements.
- Logging: each iteration appends one line to
  `tasks/<task-id>/experiments/log.md` (create it on first run).
- Iteration budget: ~5 min wall-clock per loop. If you blow past that,
  the model is too heavy or you're not committing intermediate snapshots.

## The autoresearch loop

Read `tasks/<task-id>/program.md` for the full protocol. The short
version:

1. Form one hypothesis.
2. Implement it minimally in `TASK_CONFIG["<task-id>"]` (or, deliberately,
   in the shared pipeline) inside `eval.py`.
3. Run `uv run python eval.py <task-id>` from the repo root.
4. Read score + per-hour breakdown.
5. Log a lesson.
6. Repeat.
