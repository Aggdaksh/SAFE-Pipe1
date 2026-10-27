# Git handoff across the Windows and advisor branches

## Verified branch state on 2026-10-28

`git fetch origin` and `git pull --ff-only origin main` were run on this PC. Local and remote `main` were already at `f474aae`; there were **no new main commits** to integrate into the working branch. The newer code was on `origin/codex/config-selection-policy` at feature commits `c3e328a` and `0d17438`. That branch is a direct descendant of `codex/windows-dask` and includes its 96-run study. It is now also checked out locally as `codex/config-selection-policy` and tracks its remote branch. The complete Windows suite passed 79 tests on that checkout.

To keep this PC current on the two branches without mixing them:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch codex/config-selection-policy
git pull --ff-only
git status --short --branch
```

On another PC with an existing clone, run `git fetch origin` then `git switch --track origin/codex/config-selection-policy` once. If the local branch already exists, switch to it and run `git pull --ff-only`. To inspect the two feature commits without merging, use `git log --oneline codex/windows-dask..codex/config-selection-policy` and `git diff --stat codex/windows-dask..codex/config-selection-policy` after fetching both branches. Review and merge by pull request when the team chooses its integration target; do not call the feature commits “main changes” before that merge.

The Windows work is published on `origin/codex/windows-dask`, based on the team's Mac branch `cursor/context-and-microplan`. The authorized `Aggdaksh` account pushed it on 2026-10-26. The PAT is stored locally in ignored `docs/Git.env` and must never be committed or pasted into chat.

## On this Windows PC: authenticate and push

Git is already configured on this PC. If authentication needs to be restored, run these in a PowerShell terminal with an account that can write to `Aggdaksh/SAFE-Pipe1`:

```powershell
gh auth login -h github.com -p https -w
gh auth setup-git
gh auth status
git switch codex/config-selection-policy
git push -u origin codex/config-selection-policy
```

The login command opens a browser for interactive authentication. Never paste a token into chat or a tracked repo file. If push returns 403, confirm that the signed-in account has write access to this exact repository; authentication alone is insufficient. Do not force-push or replace the remote history.

## On another PC: get this work

The newer advisor branch is already pushed. On another PC:

```powershell
git fetch origin
git switch --track origin/codex/config-selection-policy
```

If that branch already exists locally, use `git switch codex/config-selection-policy` followed by `git pull --ff-only`. To study the earlier Windows checkpoint, track `origin/codex/windows-dask` separately. Install dependencies in a local `.venv`; generated Parquet and raw JSONL are ignored. The committed `data/curated/runs.csv` is sufficient for model fitting and review. Read [`../Ganant Work.md`](../Ganant%20Work.md) and [`../context.md`](../context.md) before continuing.

For integration into `main`, review a pull request from `codex/config-selection-policy` if the team wants the measured Windows study **and** the newer advisor together. It includes the Windows and Mac-side commits it was based on. The historical `codex/windows-dask` branch remains available for comparison.
