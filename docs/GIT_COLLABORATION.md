# Git handoff for the Windows experiment branch

The Windows work is on local branch `codex/windows-dask`, based on the team's Mac branch `cursor/context-and-microplan`. The current GitHub credential for `JEENERDS` returned HTTP 403 and `gh auth status` says its token is invalid. The repository owner must grant your GitHub account write access, or the branch must be pushed to a fork and proposed as a pull request.

## On this Windows PC: authenticate and push

Run these in a PowerShell terminal after signing in with a GitHub account that can write to `Aggdaksh/SAFE-Pipe1`:

```powershell
gh auth login -h github.com -p https -w
gh auth setup-git
gh auth status
git switch codex/windows-dask
git push -u origin codex/windows-dask
```

The login command opens a browser for interactive authentication. Never paste a token into chat or a repo file. If push still returns 403, confirm that the signed-in account has write access to this exact repository; authentication alone is insufficient. Do not force-push or replace the remote history.

## On another PC: get this work

After the push succeeds:

```powershell
git fetch origin
git switch --track origin/codex/windows-dask
```

If that branch already exists locally, use `git switch codex/windows-dask` followed by `git pull --ff-only`. Install dependencies in a local `.venv`; generated Parquet and raw JSONL are ignored. The committed `data/curated/runs.csv` is sufficient for model fitting and review. Read [`../Ganant Work.md`](../Ganant%20Work.md) and [`../context.md`](../context.md) before continuing.

For integration into `main`, open a pull request from `codex/windows-dask` to `main` after the team reviews the measured results. The branch includes the Mac-side commits it was based on.
