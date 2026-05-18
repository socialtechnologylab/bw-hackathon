# Exercise 1 — Dataset integration

Your trainer has the brief on paper — that's the source of truth for
what to build, where the data lives, and how the validator works.
Read it before you start.

## Tip from the trainer

**Use test-driven development.** The remote validator runs a fixed
number of shape/content checks, but its hints are deliberately terse —
it names which check broke, never the reference value. Translating
the handout into local `pytest` cases first, then driving them red →
green, catches mistakes faster than iterating through submission
round-trips.

The repo ships with an empty `tests/` directory and `pytest` already
on `pyproject.toml`. That's the suggested workflow.

## Setup

```bash
cd exercise-1-dataset-integration
uv sync
cp .env.example .env       # paste BW_TEAM_ID from the card
claude
```
