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
| `demand-1d-ahead` | Belgium total electricity demand | MWh | 24 h |

Each task posts a separate score. The leaderboard ranks teams per-task
by their best score of the day on that task.

## Layout

```
.
├── pyproject.toml             # uv-managed deps
├── .env                       # your team credentials (gitignored)
├── eval.py                    # ONE shared baseline — covers all 3 tasks
├── .claude/                   # the starting harness — extend it
│   ├── settings.json          # permissions + acceptEdits
│   └── commands/iterate.md    # /iterate <task-id> — the autoresearch loop
├── scripts/
│   └── download_data.py       # fetch parquets for all 3 tasks
└── tasks/
    ├── solar-1d-ahead/
    │   ├── data/              # X_train, y_train, X_test, README.md
    │   ├── program.md         # the contract for this task
    │   └── experiments/log.md # your iteration log (created on first run)
    ├── wind-2h-ahead/
    └── demand-1d-ahead/
```

## The loop

```bash
uv run python eval.py <task-id>
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

The agent reads `tasks/<task-id>/program.md`, edits the corresponding
`TASK_CONFIG["<task-id>"]` entry in `eval.py`, runs it, reads the score,
logs a one-line lesson to `tasks/<task-id>/experiments/log.md`, repeats.

## Task switching

Switching tasks is free. Each task's submissions are independent on the
endpoint, and each task has its own `program.md` + `data/` + `experiments/`.
The shared `eval.py` keeps three independent `TASK_CONFIG[…]` entries —
edit only the one for the task you're working on so your hypothesis
doesn't leak across tasks.

## What you may build

Skills, slash commands, hooks, subagents, helpers, refined `program.md`s,
analysis scripts — anything that makes the loop run faster or smarter.
The starting `.claude/` ships almost empty on purpose.

## What you may not edit

- `tasks/<id>/data/*.parquet` — the data.
- `.env` — your team credentials.
