# Conventions

- Python ≥ 3.11. Package management: `uv` only. No `pip`.
- Data: `polars` for reading parquets, `pandas` only at the LightGBM
  interface boundary (`.to_pandas()`).
- ML default: `lightgbm` baseline. Anything heavier (XGBoost, sklearn
  ensembles, etc.) is fine if it fits the 5-minute per-iteration budget.
- Editing scope: only the current task's directory. Don't reach into
  other tasks. Don't touch `data/*.parquet`. Don't touch `.env`.
- Logging: each iteration appends one line to `experiments/log.md` in the
  current task dir.
- Iteration budget: ~5 min wall-clock per loop. If you blow past that,
  the model is too heavy or you're not committing intermediate snapshots.

## The autoresearch loop

Read `tasks/<task-id>/program.md` for the full protocol. The short
version:

1. Form one hypothesis.
2. Implement it minimally in `eval.py`.
3. Run it.
4. Read score + per-hour breakdown.
5. Log a lesson.
6. Repeat.
