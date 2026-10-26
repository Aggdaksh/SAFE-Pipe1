# Handoff: 16 GB experiment PC (T0 / T0b / 96-run matrix)

**Date:** 2026-10-26  
**Repo:** https://github.com/Aggdaksh/SAFE-Pipe1  
**Branch with this work:** `cursor/context-and-microplan` (merge to `main` if that is what the PC clones).

This machine is the **only** place official Dask evidence is allowed. The 8 GB Mac already has pandas tiny generators, JSONL store, optimizer tests, and the frozen 8-config grid.

## 1. Clone and install

```bash
git clone https://github.com/Aggdaksh/SAFE-Pipe1.git
cd SAFE-Pipe1
git checkout cursor/context-and-microplan
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev,dask]"
pytest
```

Record OS (Windows vs Linux), CPU, RAM, Python, Dask versions in `reports/t0.md` and `context.md`.

Disable sleep / automatic updates before overnight jobs.

## 2. T0 (must pass before anything else Dask)

```bash
python experiments/t0_smoke.py
```

Expect `ok: True` and sum `49995000`. Paste the printed dict into `reports/t0.md`.

If it fails, stop. Do not start T0b or the 96-run loop.

## 3. T0b (50 MB, 1g vs 2g)

After T0:

```bash
python experiments/t0b_probe.py --i-am-on-16gb
```

Today the script **refuses without the flag** and still **does not run Dask** even with the flag (stub exit 1). Next coding session must implement the Dask body here: generate ~50 MB `scan_filter`, time `w1_t1_1g` vs `w1_t1_2g`, write `reports/t0b.md`.

**Rules:** if 1g ≈ 2g, grow rows. Never raise `memory_limit`. If 50 MB takes > 8 minutes on 2g, freeze datasets near 80 MB.

## 4. Scale generators and collect 96 runs

Grid is frozen in `configs/dask_grid.json` (8 ids). Matrix cells: `safe_pipe.matrix.planned_cells()` → 96.

One job at a time. Shuffle order. Append JSONL. Copy `data/runs/` back to the Mac after each night.

Do **not** run this grid on the 8 GB Mac.

## 5. What the Mac already verified (do not re-prove)

- Optimizer: conformal upper bound, red OOD abstain, min cost
- 8-config grid + allocated vCPU/GB
- JSONL round-trip
- Tiny four-family Parquet + pandas execute + collector success/timeout
- `planned_cells() == 96`
- T0b guard: missing `--i-am-on-16gb` exits 2

## 6. Still not implemented (do not fake results)

Dask execute path for the four families, LightGBM, conformal fit, OOD, SHAP, TabPFN, Glue.
