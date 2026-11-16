# One-probe Windows handoff: software checks only

The [feasibility comparison](../../reports/one_probe_feasibility_20261116/README.md) is complete. A single quarter-size probe still adds cost without changing the metadata choices on current jobs. **Do not launch the proposed 48-attempt pilot, Stage C, dataset generation or training.** The research branch's original raw data stays untouched.

The new decision module, targeted synthetic tests and checks-only CLI are prepared. They were statically parsed/compiled on the Mac; Windows runtime verification is still pending. No tests are reported as passed until Windows produces the output below.

## Commands on Windows

In the existing repository on `codex/partition-probe-research`, with a clean working tree, pull the latest research branch using a fast-forward update. Keep the existing research environment unchanged. From the repository root:

```powershell
git status --short --branch
git pull --ff-only origin codex/partition-probe-research
.\.venv-research\Scripts\python.exe -m experiments.verify_one_probe --out reports/one_probe_windows_checks_v1
```

If there are local edits, preserve them and resolve the sync deliberately; do not reset/clean or overwrite them. If the output directory already exists, use a new suffixed directory rather than deleting the previous verification attempt.

The CLI is Windows-only and:

1. Runs only `tests/test_one_probe.py`, retaining stdout/stderr in `WINDOWS_TEST_OUTPUT.txt`.
2. Checks normalized input hashes against the frozen feasibility artifact. It does not rewrite saved Windows raw hashes.
3. Checks eight default metadata decisions with probe admission disabled, then 24 separate single-observation **counterfactual** decisions against the standalone analysis. These are software replays, not 24 new probes or independent workloads.
4. Checks all 37 retained termination records remain explicitly non-exact memory observations.
5. Writes `verification.json` and `README.md`, records source fingerprints/revision and stops. No Dask runner, generator or model is invoked. Runtime estimates used to exercise the disabled gate are marked synthetic and cannot enable it.

A failed command produces no permission to rerun physical experiments. Preserve the failure output, fix the code and repeat checks into a new report directory. A successful command validates software behavior against existing evidence only; it does not open the research feasibility gate.

## Return evidence

Commit the generated report directory, plus any reviewed fixes and a short `context.md` status update, to the same research branch and push it. Keep `admission_enabled=false` and the draft pilot disabled. Do not stage raw Parquet/JSONL, local credentials or ignored environment files; do not merge main.

After software verification, the next research deliverable is a revised method/use-case proposal with a credible information/economics argument and closest-work comparison. There is currently **no next benchmark command**. The proposed physical runner is deliberately deferred because the gate failed, rather than presented as ready to execute.
