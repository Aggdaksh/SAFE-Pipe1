# Git handoff for the Windows experiment branch

The Windows work is published on `origin/codex/windows-dask`, based on the team's Mac branch `cursor/context-and-microplan`. The authorized `Aggdaksh` account pushed it on 2026-10-26. The PAT is stored locally in ignored `docs/Git.env` and must never be committed or pasted into chat.

## On this Windows PC: authenticate and push

Git is already configured on this PC. If authentication needs to be restored, run these in a PowerShell terminal with an account that can write to `Aggdaksh/SAFE-Pipe1`:

```powershell
gh auth login -h github.com -p https -w
gh auth setup-git
gh auth status
git switch codex/windows-dask
git push -u origin codex/windows-dask
```

The login command opens a browser for interactive authentication. Never paste a token into chat or a tracked repo file. If push returns 403, confirm that the signed-in account has write access to this exact repository; authentication alone is insufficient. Do not force-push or replace the remote history.

## On another PC: get this work

The branch is already pushed. On another PC:

```powershell
git fetch origin
git switch --track origin/codex/windows-dask
```

If that branch already exists locally, use `git switch codex/windows-dask` followed by `git pull --ff-only`. Install dependencies in a local `.venv`; generated Parquet and raw JSONL are ignored. The committed `data/curated/runs.csv` is sufficient for model fitting and review. Read [`../Ganant Work.md`](../Ganant%20Work.md) and [`../context.md`](../context.md) before continuing.

For integration into `main`, open a pull request from `codex/windows-dask` to `main` after the team reviews the measured results. The branch includes the Mac-side commits it was based on.
