# BW Hackathon

Two-exercise workshop on building agentic harnesses around forecasting
work. You clone this repo once; each exercise lives in its own
self-contained subdirectory with its own `uv` project, its own
`.claude/` permissions, its own README, and its own contract.

```bash
git clone https://github.com/socialtechnologylab/bw-hackathon
cd bw-hackathon
```

## The exercises

| When | Directory | What |
|---|---|---|
| Morning | [`exercise-1-dataset-integration/`](./exercise-1-dataset-integration/) | Pull an obscure-format public dataset (ECMWF Open Data, GRIB2) and shape it into two validated parquets — a raw spatial-mean series and a model-ready (hourly, z-scored) features table. You write your own pytest cases against the brief; the remote validator at `bw.stl.dev/exercise-1/submit` is the binding judge. |
| Afternoon | [`exercise-2-autoresearch/`](./exercise-2-autoresearch/) | Build the harness around an autoresearch loop and point it at three Belgian electricity-forecasting tasks served by a live scoring endpoint. Each `eval.py` run is a real submission; the leaderboard ranks teams per task by best MAE. The harness you build *is* what's being graded. |

Each exercise has its own `README.md` with the full contract. Start there.

## How to run an exercise

Always `cd` into the exercise's subdirectory **before** launching `claude`.
Each exercise ships its own `.claude/settings.json` with the permissions
your agent needs (uv, pytest, curl https, file ops, …) — those only get
picked up when Claude Code is started from inside the directory that
contains the `.claude/` folder.

```bash
cd exercise-1-dataset-integration       # or exercise-2-autoresearch
uv sync
cp .env.example .env                    # paste BW_TEAM_ID from the card
claude
```

If you launch `claude` from the repo root, you'll be hammered by
permission prompts on every Bash call. `cd` first.

## Operating posture

- Your agent is doing the work. You are building the harness around it.
- Each exercise ships a *minimal* `.claude/` — just the permissions plumbing
  (and, for Exercise 2, a starter `/iterate` slash command). Extend it
  with skills, hooks, helpers, and subagents as you go. The bare
  starting state is on purpose.
- Don't peek at the next exercise before the trainer opens it. The
  practice is in doing each one fresh.
- `uv` only for Python; never `pip`. Each exercise has its own
  `pyproject.toml` and its own venv.

## What you need on your machine

- macOS or Linux (Windows users: WSL).
- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)).
- `claude` CLI ([install](https://docs.anthropic.com/en/docs/claude-code/quickstart)).
