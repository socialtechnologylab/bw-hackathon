# Exercise 2 — Autoresearch hackathon

Three minutes from a clean directory to running:

```bash
uv sync
cp .env.example .env       # paste BW_TEAM_ID + BW_TEAM_TOKEN from the card you were handed
uv run python scripts/download_data.py
claude
> /iterate solar-1d-ahead
```

## What this is

An autoresearch hackathon. You're not optimising a model directly — you're
building the harness around an agent that optimises models for you, then
sending it loose on forecasting tasks. The harness you build *is* the
artefact being graded.

## The three tasks

| Task ID | What | Unit | Lead time |
|---|---|---|---|
| `solar-1d-ahead` | Belgium solar generation | MWh | 24 h |
| `wind-2h-ahead` | Belgium wind generation (onshore + offshore) | MWh | 2 h |
| `demand-1d-ahead-test` | Belgium total electricity demand | MWh | 24 h |

Each task posts a separate score. The leaderboard ranks teams per-task
by their best score of the day on that task. `demand-1d-ahead-test`
is locked until the trainer reveals it (you'll see `reveal_at` in
`GET /tasks`).

## Layout

```
.
├── pyproject.toml             # uv-managed deps
├── .env                       # your team credentials (gitignored)
├── .claude/                   # the starting harness — extend it
│   ├── settings.json          # permissions + acceptEdits
│   └── commands/iterate.md    # /iterate <task-id> — the autoresearch loop
├── scripts/
│   └── download_data.py       # fetch parquets for all 3 tasks
└── tasks/
    ├── solar-1d-ahead/
    │   ├── eval.py            # self-contained script — your edit surface
    │   ├── program.md         # the contract for this task
    │   └── data/              # X_train, y_train, X_test, README.md
    ├── wind-2h-ahead/
    │   ├── eval.py
    │   ├── program.md
    │   └── data/
    └── demand-1d-ahead-test/
        ├── eval.py
        ├── program.md
        └── data/
```

## The loop

```bash
cd tasks/solar-1d-ahead && uv run python eval.py
```

…trains a model on the task's parquets, posts predictions to the scoring
endpoint, prints the MAE plus a breakdown by hour of day. Each run is a
submission; your team's `best_so_far` on a task is the lowest MAE
across all your submissions today. **Lower MAE = better.**

From inside `claude`:

```
> /iterate solar-1d-ahead       # work on solar
> /iterate wind-2h-ahead         # switch to wind anytime
```

The agent reads `tasks/<task-id>/program.md`, edits
`tasks/<task-id>/eval.py`, runs it, reads the score, and commits with
the MAE delta in the message. `git log --oneline -- tasks/<task-id>/eval.py`
becomes the per-task experiment journal.

## Task switching

Switching tasks is free. Each task's submissions are independent on
the endpoint, and each task has its own `eval.py` + `program.md` +
`data/`. Stay inside your task's directory while iterating so changes
don't bleed across tasks.

## What you may build

Skills, slash commands, hooks, subagents, helpers, refined `program.md`s,
analysis scripts — anything that makes the loop run faster or smarter.
The starting `.claude/` ships almost empty on purpose.

## What you may not edit

- `tasks/<id>/data/*.parquet` — the data.
- `.env` — your team credentials.
- Other tasks' `eval.py` files. One task at a time.
