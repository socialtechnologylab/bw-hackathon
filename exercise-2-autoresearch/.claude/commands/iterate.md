---
description: Run the autoresearch loop on a task — usage `/iterate <task-id>`. Reads tasks/<task-id>/program.md, edits eval.py, re-runs, logs lessons.
argument-hint: <task-id>  (solar-1d-ahead | wind-2h-ahead | demand-1d-ahead)
---

You are inside an autoresearch loop on the forecasting task `$ARGUMENTS`.

If `$ARGUMENTS` is empty, stop and ask which task to work on. Valid ids:
`solar-1d-ahead`, `wind-2h-ahead`, `demand-1d-ahead`.

Working directory for this loop is `tasks/$ARGUMENTS/`. All edits, runs,
and lesson logs happen there.

1. Read `tasks/$ARGUMENTS/program.md`. That document defines the loop,
   what you may edit, what you may not, and what the score means.
2. Read `tasks/$ARGUMENTS/eval.py`. Form a single concrete hypothesis
   about what would improve the score — better features, model choice,
   hyperparameters, lag features, calibration.
3. Edit `tasks/$ARGUMENTS/eval.py` to implement that hypothesis. Keep
   the change small and isolated.
4. Run `cd tasks/$ARGUMENTS && uv run python eval.py`. Read the score,
   the raw metric, and the per-hour breakdown.
5. Append one line to `tasks/$ARGUMENTS/experiments/log.md` (create it
   if it doesn't exist): the hypothesis, the score before and after,
   and what you learned.
6. Goto 2.

Continue until told to stop, or until you've made five iterations
without improving `best_so_far`. If you stall, say so and pause for
guidance rather than thrashing.

Do not edit `tasks/$ARGUMENTS/data/*.parquet`, `.env`, or files outside
the current task directory.

To switch tasks mid-session, just run `/iterate` again with a different
task id — submissions accumulate per team per task on the leaderboard
and your best score on each task is preserved.
