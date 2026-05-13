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
2. Implement it minimally in `TASK_CONFIG["<task-id>"]` (or, deliberately,
   in the shared pipeline) inside `eval.py`.
3. Run `uv run python eval.py <task-id>` from the repo root.
4. Read score + per-hour breakdown.
5. Commit with the result in the message — see `/iterate` for the format.
6. Repeat.

Commit messages should read like a lab notebook. Lowercase terse
subjects (`solar-1d-ahead: add sin/cos(hour) encoding`), MAE delta in
the body. Commit failures too. `git log --oneline` is the journal.
