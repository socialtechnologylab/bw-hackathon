# Conventions

- Python ≥ 3.11. Package management: `uv` only. No `pip`.
- Data: `polars` for reading parquets, `pandas` only at the LightGBM
  interface boundary (`.to_pandas()`).
- ML default: `lightgbm` baseline. Anything heavier (XGBoost, sklearn
  ensembles, etc.) is fine if it fits the 5-minute per-iteration budget.
- Editing scope: **each task's `eval.py` is a self-contained script.**
  Edit `tasks/<task-id>/eval.py` for the task you're working on. Stay
  out of other tasks' scripts. Don't touch `tasks/*/data/*.parquet` or
  `.env`.
- Logging: **git commits ARE the experiment journal.** One commit per
  iteration, lowercase terse subject, MAE delta + one-line lesson in
  the body. See `/iterate` for the format. No separate log file.
  Commit failures too — negative results are data.
- Iteration budget: ~5 min wall-clock per loop. If you blow past that,
  the model is too heavy or you're not committing intermediate snapshots.

## The autoresearch loop

Read `tasks/<task-id>/program.md` for the full protocol. The short
version (karpathy-tight: one hypothesis, one run, one commit):

1. Form one hypothesis.
2. Implement it minimally in `tasks/<task-id>/eval.py`.
3. `cd tasks/<task-id> && uv run python eval.py`.
4. Read score + per-hour breakdown.
5. Commit with the result in the message — see `/iterate` for the format.
6. Repeat.

Commit messages should read like a lab notebook. Lowercase terse
subjects (`solar-1d-ahead: add sin/cos(hour) encoding`), MAE delta in
the body. Commit failures too. `git log -- tasks/<task-id>/eval.py`
gives you that task's journal.
