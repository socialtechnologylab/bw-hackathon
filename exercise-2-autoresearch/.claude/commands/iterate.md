---
description: Karpathy-style autoresearch loop on a task. One hypothesis, one tiny edit, one run, one commit. Usage `/iterate <task-id>`.
argument-hint: <task-id>  (solar-1d-ahead | wind-1d-ahead | demand-1d-ahead-test)
---

You are inside an autoresearch loop on `$ARGUMENTS`.

If `$ARGUMENTS` is empty, stop and ask. Valid ids: `solar-1d-ahead`,
`wind-1d-ahead`, `demand-1d-ahead-test`.

Working directory: `tasks/$ARGUMENTS/`. The whole experiment for this
task lives in a single file there:

    tasks/$ARGUMENTS/
    ├── eval.py         ← your only edit surface
    ├── program.md      ← the task brief
    └── data/           ← parquets (don't touch)

## The loop

One hypothesis → one tiny edit → one run → one commit. `git log --oneline`
is your experiment journal. There is no separate `log.md`.

1. (Once, first iteration only.) Read `tasks/$ARGUMENTS/program.md`.
2. Form **one** concrete hypothesis. Smaller diff = better.
3. Edit `tasks/$ARGUMENTS/eval.py`. Go wild — it's a self-contained
   script. Features, model, transforms, ensembles, calibration, whatever.
4. Run it:

       cd tasks/$ARGUMENTS && uv run python eval.py

   Read the MAE and the per-hour breakdown.
5. Commit immediately, regardless of whether the score improved:

       git add tasks/$ARGUMENTS/eval.py
       git commit -m "$ARGUMENTS: <terse description of the change>" \
                  -m "MAE <before> → <after>. <one-sentence lesson>"

6. Goto 2.

## Commit-message discipline (karpathy)

Look at `karpathy/nanochat` commit log for the vibe. Specifically:

- **Lowercase, terse subject lines.** No `feat:` / `fix:` prefixes.
  This is a lab notebook, not a changelog.
- **Commit failures.** `solar-1d-ahead: tried huber loss, MAE got worse`
  is a perfectly good commit. Negative results are data.
- **Batch related dead-ends** under one commit when they share a theme:
  `solar-1d-ahead: bunch of feature crosses tried, all neutral`.
- **Put numbers in the body.** Reading `git log --oneline -p tasks/$ARGUMENTS/`
  later should let you reconstruct the experiment trajectory.
- **No ceremony.** Don't write "this commit adds…". Just say what
  happened: `add sin/cos(hour) encoding, MAE 333.66 → 318.52`.

## Rewinding

If a change made things much worse and you want to abandon it cleanly:

    git reset --hard HEAD^      # back up one commit
    # then try a different direction

Leaving the bad commit is also fine — it's history. Use `reset` when
the bad result is uninteresting, keep the commit when it's instructive.

## Stop conditions

- User says stop.
- Five consecutive commits with no improvement in `best_so_far`.
- You can't articulate the next move as a single hypothesis. Pause
  and surface what you've learned rather than thrashing.

## Don't

- Edit other tasks' `eval.py`. Each task is its own surface; stay in
  yours.
- Edit `tasks/<id>/data/*.parquet` or `.env`.
- Skip the commit, even on a regression.

## Task switching

`/iterate` again with a different task id. Submissions accumulate per
team per task on the leaderboard; your best score on each task is
preserved across the day. `git log -- tasks/<id>/eval.py` gives you
the per-task history at any time.
