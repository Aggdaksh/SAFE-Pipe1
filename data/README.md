Generated Parquet and JSONL live here locally and are gitignored (`data/generated/`, `data/runs/`).

Create them with:

```bash
safe-pipe generate --dest data/generated
safe-pipe collect --family scan_filter --store data/runs/runs.jsonl
```

Do not commit `*.parquet` or run logs.
