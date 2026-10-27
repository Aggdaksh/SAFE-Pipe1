# Git collaboration guide

## Current state (28 October 2026)

The Windows study and explained advisor are integrated into `main`. On this PC, `main` was fast-forwarded from `f474aae` to `abb21f7`, tested (**79 passed**), and pushed to `origin/main`. The former `codex/windows-dask` and `codex/config-selection-policy` branches remain published checkpoints; their commits are already in `main`.

The integrated work includes the 96-run local Dask study, curated CSV, runtime model and artifacts, CLI demo, three advisor modes, exact frozen-profile support gate, data dictionary, and independent-validation plan. The advisor's 20-scenario replay reuses the 96 measured rows; it is not a new physical experiment. See [PROGRESS](../PROGRESS.md) and [Ganant's log](../Ganant%20Work.md).

## Update an existing clone on any PC

Save or commit your own edits first, then run:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git status --short --branch
```

`--ff-only` stops if your local `main` has diverged, preserving your commits for review. If you have local edits that prevent switching or pulling, inspect `git status`, then commit them on a topic branch or stash them before retrying. Do not force-push shared history.

For a fresh clone, clone `Aggdaksh/SAFE-Pipe1`, switch to `main`, and install the dependencies described in [README](../README.md). Each PC needs its own virtual environment. Git includes the curated `data/curated/runs.csv` and model artifacts; generated Parquet inputs, raw JSONL runs, `.venv`, and credentials are ignored.

## Continue work and publish it

Start a new topic branch from updated `main` so teammates can review a focused change:

```powershell
git switch main
git pull --ff-only origin main
git switch -c your-topic-name
# make changes, run relevant checks, then review git status and git diff
git add <specific-files>
git commit -m "Describe the change"
git push -u origin your-topic-name
```

Then open a pull request targeting `main`. After review and merge, each PC should pull `main` again. The historical Windows and advisor branches do not need another merge.

## Authentication on Ganant's Windows PC

GitHub CLI authentication is already configured for the `Aggdaksh` account with repository write access. If credentials need restoring, use `gh auth login -h github.com -p https -w`, followed by `gh auth setup-git` and `gh auth status`. A 403 means the signed-in account may lack write permission to this repository.

The local PAT file `docs/Git.env` is ignored. Never add it to Git, paste its value into chat, or include it in a screenshot. Use `git status` and `git diff --cached` to check a commit before pushing.
