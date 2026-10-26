Generated Parquet, physical JSONL, and demo inputs live here locally and are gitignored (`data/generated/`, `data/runs/`, `data/demo/`). The audited 96-row `curated/runs.csv` and `curated/audit.json` are committed for cross-PC model work. `curated/runs.parquet` is generated locally and ignored.

Create them with:

```bash
safe-pipe generate --dest data/generated
safe-pipe collect --family scan_filter --store data/runs/runs.jsonl
```

Do not commit `*.parquet` or raw run logs. See `../reports/audit.md` for hashes and provenance. The Mac-side tiny commands below are historical; `../reports/demo.md` has the verified Windows Dask demo.
