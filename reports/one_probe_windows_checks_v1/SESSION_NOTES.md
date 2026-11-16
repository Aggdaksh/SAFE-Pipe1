# Windows checks-only session

- Date: 2026-11-16. Source revision: `82d40af89c681644ecc4a221c7b09f58ef964441`, branch `codex/partition-probe-research`.
- Synced by fast-forward from `c8872b4`; pre-existing untracked `output/` and `tools/` preserved. Used the existing research environment without installing or updating packages.
- Ran the requested command once from the repository root:

  ```powershell
  .\.venv-research\Scripts\python.exe -m experiments.verify_one_probe --out reports/one_probe_windows_checks_v1
  ```

- Result: **PASS**, process exit code 0. [Actual targeted test output](WINDOWS_TEST_OUTPUT.txt): **38 passed in 0.23 s**. [Verification details](verification.json): eight default decisions, 24 separate single-observation counterfactual decisions and 37 event-aware termination records checked. Each termination observation remains non-exact and ineligible as an automatic regression target.
- The verifier checked normalized existing-evidence hashes against the frozen feasibility artifact and captured source SHA-256/revision. Independent before/after byte-hash comparison covered **1,513 unchanged files**: four raw Stage A/B plan/JSONL files, 1,507 retained diagnostic files and two checked-in policy/pilot-draft files. Dataset bytes were not reread; no files were generated in original raw directories.
- Parsed the saved report/output again to confirm the 38/8/24/37 counts, eight no-probe defaults, zero physical attempts, disabled admission/pilot and public artifact scan. No code fixes, policy changes, threshold/evidence changes or verification reruns were needed. Existing verification folders were not overwritten.
- No Dask jobs, 48-run pilot, Stage C, dataset generation, training or main merge. Synthetic tests exercise enabled-policy branches only on in-memory copies; checked-in `admission_enabled=false`, draft `enabled=false` and `runner_implemented=false` remain unchanged.
- Passing software verification does not establish new policy value, independent performance validation or permission to start experiments. The next research deliverable is a revised method/use-case proposal with incremental information, credible all-cost economics and closest-work comparison.
