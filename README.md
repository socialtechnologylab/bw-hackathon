# BW Hackathon

Two-exercise workshop on building agentic harnesses around forecasting
work. You clone this repo once; each exercise lives in its own
self-contained subdirectory with its own `uv` project, its own README,
and its own validator.

```bash
git clone https://github.com/socialtechnologylab/bw-hackathon
cd bw-hackathon
```

## The exercises

| When | Directory | What |
|---|---|---|
| Morning | [`exercise-1-dataset-integration/`](./exercise-1-dataset-integration/) | Pull an obscure-format public dataset (ECMWF Open Data, GRIB2) and shape it into a validated parquet. Tests in `tests/` decide whether you're done. |
| Afternoon | [`exercise-2-autoresearch/`](./exercise-2-autoresearch/) | Build the harness around an autoresearch loop and point it at three Belgian electricity-forecasting tasks served by a live scoring endpoint. The harness you build *is* what's being graded. |

Each exercise has its own `README.md` with the contract. Start there.

## Operating posture

- Your agent is doing the work. You are building the harness around it.
- Both exercises ship deliberately empty `.claude/` (or absent
  altogether) — extend it with skills, slash commands, hooks, helpers,
  and subagents as you go.
- Don't peek at the next exercise before the trainer opens it. The
  practice is in doing each one fresh.
- `uv` only for Python; never `pip`. Each exercise has its own
  `pyproject.toml` — `cd` in and `uv sync` first.

## What you need on your machine

- macOS or Linux (Windows users: WSL).
- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)).
- `claude` CLI ([install](https://docs.anthropic.com/en/docs/claude-code/quickstart)).
- For Exercise 1: a system-level GRIB decoder. On macOS:
  `brew install eccodes`. On Debian/Ubuntu: `apt install libeccodes-dev`.
  (Discovering this requirement is part of the exercise — but you'll
  want it on disk before the morning starts.)
