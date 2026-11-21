# Windows verification checkpoint

Date: 2026-11-21 (Asia/Calcutta). Branch: `codex/main-advisor-completion`.

## Tested implementation and result

- Tested commit: `d6f906a6f69ea6893d8ebab3d38b6dd1a0ced8eb`.
- Existing original-advisor environment: repository `.venv`, CPython 3.14.6, Windows 11 AMD64. The exact interpreter command, platform, host and package versions are in `verification.json`.
- Command: `.\.venv\Scripts\python.exe -m experiments.verify_main_validation --out reports/main_validation_windows_checks_v1`.
- First attempt; the output directory did not exist before this invocation.
- Dependency check: exit 0, `No broken requirements found.`
- Full software suite, including tiny Dask integration fixtures: **143 collected, 143 passed, 0 failed, 0 errors, 0 skipped; 36.89 seconds**. Pytest exit 0.
- Verification result: **PASS**. No implementation fixes, dependency installs or upgrades were needed.

## Evidence and preservation checks

The verifier's original five outputs are retained without rewriting: `verification.json`, `PIP_CHECK.txt`, `WINDOWS_TEST_OUTPUT.txt`, `tests.xml`, and `README.md`. This note adds context without changing the machine-readable receipt.

The saved JUnit counts were independently compared with the receipt. All 78 normalized source/evidence hashes and the package/platform environment still matched after verification. The receipt records zero fresh study cells executed.

Before/after byte hashes matched for 14 files: `pyproject.toml`, the original `artifacts/main_v1/` files, curated files, and main-v1 `manifest.json` files. The 70-file original `data/generated/main-v1/` inventory retained identical paths, sizes and modification timestamps. This inventory check does not claim a new content-hash audit of every Parquet file. Full original-input hashing remains part of future study preparation.

The working tree initially had no tracked modifications. Existing unrelated untracked `output/` and `tools/` directories were preserved and excluded from this evidence commit. The research branch remains separate; only this completion branch was fast-forward synchronized. No credentials or raw datasets are included.

## Scope and next gate

Only software verification ran. Tiny temporary test fixtures are part of the suite; there was no fresh 96-run experiment, original dataset regeneration, model training, or main merge. No fresh-study preparation command was executed.

The checkpoint is ready for user evidence review. Study preparation and physical collection remain future steps; a passing software receipt alone does not establish advisor accuracy on fresh measurements or authorize starting experiments.
