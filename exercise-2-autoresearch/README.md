# Exercise 2 — Autoresearch hackathon

You're forecasting three Belgian electricity series — how much solar
will be produced tomorrow, how much wind in two hours, how much demand
the country will draw — and your job is **not** to tune the model by
hand. Your job is to build a harness around a Claude agent so it can
tune, hypothesise, and submit faster than the next team's harness.

Each task ships its own self-contained `tasks/<task-id>/eval.py`:
train a model, predict, POST to the live scoring endpoint, get back a
real MAE. The leaderboard ranks per task by lowest MAE. The harness
you build — slash commands, hooks, helpers, refined briefs, subagents
— is what's being graded.

Three minutes from clean directory to first submission:

```bash
uv sync
cp .env.example .env       # paste BW_TEAM_ID + BW_TEAM_TOKEN from your card
uv run python scripts/download_data.py
claude
> /iterate solar-1d-ahead
```

## The three tasks

| Task ID | What | Lead time |
|---|---|---|
| `solar-1d-ahead` | Belgian solar generation | 24 h |
| `wind-2h-ahead` | Belgian wind generation (onshore + offshore) | 2 h |
| `demand-1d-ahead-test` | Belgian total electricity demand | 24 h |

`demand-1d-ahead-test` is the **late-reveal** task — it stays locked
until the trainer opens it (the leaderboard for it is empty until
then, and `/score` returns HTTP 423 with the unlock time). Spend the
morning on solar and wind.

## Where to find the data contract

Don't trust this README to be authoritative for column names, dtypes,
or units. The endpoint is. Fetch a task's full data contract from:

```bash
curl https://bw.stl.dev/tasks/solar-1d-ahead/schema | jq
```

That tells you the target column, cadence, train/test windows, every
feature column with its dtype and unit, and the upstream data sources.
Have your agent read it before iterating.

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
    │   ├── program.md         # the loop contract for this task
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

…trains a model on the task's parquets, posts predictions to the
scoring endpoint, prints the MAE plus a breakdown by hour of day.
Each run is a real submission. Your team's `best_so_far` on a task
is the lowest MAE across all your submissions today. **Lower MAE =
better.**

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

Switching tasks is free. Each task has its own `eval.py`,
`program.md`, and `data/`. Submissions accumulate per team per task
on the leaderboard; the locked demand task accepts no submissions
until reveal.

## A few directions to try

Stuck on what to ask your agent to try next? Some seed prompts (far
from exhaustive — most of the fun is in what you come up with):

**Feature engineering** — usually the cheapest wins
- Cyclical encoding of `hour` / `dow` / `month`: `sin(2π·h/24)`, `cos(2π·h/24)` (so 23 → 0 is one step, not 23).
- Effective insolation: `ghi_fcst × (1 − cloud_cover_fcst)` — closer to what panels actually see.
- Lag features: `t2m_fcst` shifted 3 / 6 / 24 hours back; `polars.shift` is a one-liner.
- Forecast×calendar interactions: `hour * ghi_fcst`, `month * t2m_fcst`.

**Bring in new data sources** — the schema only lists what we ship; you can add anything
- Belgian holidays via [`python-holidays`](https://pypi.org/project/holidays/) — demand drops on bank holidays.
- Day-ahead electricity prices via [`entsoe-py`](https://github.com/EnergieID/entsoe-py) — strong demand covariate (you'll need a free ENTSO-E token).
- Sun elevation via [`astral`](https://astral.readthedocs.io/) — the actual solar geometry behind GHI.
- Neighbouring countries' generation/demand via ENTSO-E — cross-border drivers.

**Try a different model**
- LightGBM hyperparam sweep: bigger `n_estimators`, smaller `learning_rate`, tune `num_leaves` / `min_data_in_leaf`.
- Swap in `xgboost` or `catboost`. Same `.fit/.predict` interface.
- Quantile regression on the residuals to correct per-hour bias.
- Stack: average LightGBM + a per-hour mean baseline.

**Tune the agent itself** — `.claude/` is yours to extend
- Tighten `/iterate`: only commit on improvement, or auto-tag failures with `bad:`.
- Add an `/ablate` slash command that drops one feature at a time and reports the MAE delta per feature.
- Pre-`/score` hook that runs `eval.py` locally first and refuses to submit if MAE got worse.
- Subagent for parallel hypothesis exploration on a different task.
- Custom skill that summarises the last N commits and proposes the next direction.

The starting `.claude/` ships almost empty on purpose. The harness you
build is the artefact being graded — model tweaks alone don't win.

## What you may not edit

- `tasks/<id>/data/*.parquet` — the data.
- `.env` — your team credentials.
- Other tasks' `eval.py` files. One task at a time.

## Endpoints reference

| Endpoint | What |
|---|---|
| `GET /healthz` | liveness check |
| `GET /tasks` | the three task ids with their metric and reveal-time status |
| `GET /tasks/{task_id}/schema` | full data contract (columns, dtypes, units, windows) |
| `POST /score` | submit predictions (your `eval.py` does this) |
| `GET /leaderboard?task_id=…` | ranked teams for a task, ascending by MAE |
