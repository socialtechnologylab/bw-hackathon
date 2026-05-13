---
description: Run the autoresearch loop on a task — usage `/iterate <task-id>`. Reads tasks/<task-id>/program.md, edits the TASK_CONFIG entry in eval.py, re-runs, logs lessons.
argument-hint: <task-id>  (solar-1d-ahead | wind-2h-ahead | demand-1d-ahead)
---

You are inside an autoresearch loop on the forecasting task `$ARGUMENTS`.

If `$ARGUMENTS` is empty, stop and ask which task to work on. Valid ids:
`solar-1d-ahead`, `wind-2h-ahead`, `demand-1d-ahead`.

Working directory for this loop is the **repo root**. The shared
`eval.py` at the root drives all three tasks via a `TASK_CONFIG` dict;
each task has its own per-task brief in `tasks/<task-id>/program.md`
and its own iteration log in `tasks/<task-id>/experiments/log.md`.

1. Read `tasks/$ARGUMENTS/program.md`. That document defines the loop,
   what you may edit, what you may not, and what the score means.
2. Read `eval.py`. Find the `TASK_CONFIG["$ARGUMENTS"]` entry. Form a
   single concrete hypothesis about what would improve the score —
   better features, model choice, hyperparameters, lag features,
   calibration.
3. Edit **only** the `TASK_CONFIG["$ARGUMENTS"]` entry in `eval.py` to
   implement that hypothesis. Leave the other tasks' entries and the
   shared pipeline alone unless the change is deliberately cross-task.
4. Run `uv run python eval.py $ARGUMENTS` from the repo root. Read the
   score, the raw metric, and the per-hour breakdown.
5. Append one line to `tasks/$ARGUMENTS/experiments/log.md` (create it
   if it doesn't exist): the hypothesis, the score before and after,
   and what you learned.
6. Goto 2.

Continue until told to stop, or until you've made five iterations
without improving `best_so_far`. If you stall, say so and pause for
guidance rather than thrashing.

Do not edit `tasks/<id>/data/*.parquet`, `.env`, or other tasks'
`TASK_CONFIG` entries. The shared submission/reporting pipeline below
`TASK_CONFIG` in `eval.py` is fair game if you have a cross-task
improvement — but be deliberate, since changing it affects every task
you run after.

To switch tasks mid-session, just run `/iterate` again with a different
task id — submissions accumulate per team per task on the leaderboard
and your best score on each task is preserved.
