# Exercise 2 — Autoresearch hackathon

You're forecasting three Belgian electricity time series (solar energy generation, wind energy generation and electricity deman). Your job is **not** to tune the model by
hand. Your job is to build a harness and task for a Claude agent so it can
tune, hypothesise, and submit autonomously better than the next team's harness.

Each task ships its own self-contained `tasks/<task-id>/eval.py`:
train a model, predict, POST to the live scoring endpoint, get back a
real MAE. The leaderboard ranks per task by lowest MAE.

Three minutes from clean directory to first submission:

```bash
uv sync
cp .env.example .env       # paste BW_TEAM_ID from your card
uv run python scripts/download_data.py
claude
> /iterate solar-1d-ahead
```

## The three tasks

| Task ID | What | Lead time |
|---|---|---|
| `solar-1d-ahead` | Belgian solar generation | 24 h |
| `wind-1d-ahead` | Belgian wind generation (onshore + offshore) | 24 h |
| `demand-1d-ahead-test` | Belgian total electricity demand | 24 h |

`demand-1d-ahead-test` is the **late-reveal** task which you will be graded on. It stays locked
until the trainer opens it, you then have half an hour to make the best predictions you can. Spend time optimizing on solar and wind to practice and experiment

## Where to find the data contract

Don't trust this README to be authoritative for column names, dtypes,
or units. The endpoint is. Fetch a task's full data contract from:

```bash
curl https://bw.stl.dev/tasks/solar-1d-ahead/schema | jq
```

That tells you the target column, cadence, train/test windows, every
feature column with its dtype and unit, and the upstream data sources.

## Layout

```
.
├── pyproject.toml             # uv-managed deps
├── .env                       # your team identifier (gitignored)
├── .claude/                   # the starting harness — extend it
│   ├── settings.json          # permissions + acceptEdits
│   └── commands/iterate.md    # /iterate <task-id> — the autoresearch loop
├── scripts/
│   └── download_data.py       # fetch data for all 3 tasks
└── tasks/
    ├── solar-1d-ahead/
    │   ├── eval.py            # self-contained script — your edit surface
    │   ├── program.md         # the loop contract for this task
    │   └── data/              # X_train, y_train, X_test, README.md
    ├── wind-1d-ahead/
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

…trains a model on the task's parquets, posts predictions to the
scoring endpoint, prints the MAE plus a breakdown by hour of day.
Each run is a real submission. Your team's `best_so_far` on a task
is the lowest MAE across all your submissions today. **Lower MAE =
better.**

From inside `claude`:

```
> /iterate solar-1d-ahead       # work on solar
> /iterate wind-1d-ahead         # switch to wind anytime
```

The agent reads `tasks/<task-id>/program.md`, edits
`tasks/<task-id>/eval.py`, runs it, reads the score, and commits with
the MAE delta in the message. `git log --oneline -- tasks/<task-id>/eval.py`
becomes the per-task experiment journal.

## Task switching

Switching tasks is free. Each task has its own `eval.py`,
`program.md`, and `data/`. Submissions accumulate per team per task
on the leaderboard; the locked demand task accepts no submissions
until reveal.

## A few directions to try

Some shapes of things worth exploring — your agent will fill in the
specifics:

- **Feature engineering.** The features we ship are forecast variables
  + raw calendar fields. Plenty of structure they don't encode.
- **New data sources.** The schema only lists what we hand you;
  nothing stops you from pulling in something else that might help.
- **Different model.** LightGBM with the default hyperparameters is the
  baseline, not the ceiling.
- **Calibration.** The `eval.py` already prints a per-hour breakdown —
  patterns there tend to be actionable.
- **Tune the agent itself.** `/iterate`, hooks, subagents, custom
  skills — the starting `.claude/` is deliberately sparse. The harness
  you build is the artefact being graded; model tweaks alone don't
  win.

## What you may not edit

- `tasks/<id>/data/*.parquet` — the data.
- `.env` — your team identifier.
- Other tasks' `eval.py` files. One task at a time.

## Endpoints reference

| Endpoint | What |
|---|---|
| `GET /healthz` | liveness check |
| `GET /tasks` | the three task ids with their metric and reveal-time status |
| `GET /tasks/{task_id}/schema` | full data contract (columns, dtypes, units, windows) |
| `POST /score` | submit predictions (your `eval.py` does this) |
| `GET /leaderboard?task_id=…` | ranked teams for a task, ascending by MAE |
