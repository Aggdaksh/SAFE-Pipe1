# Research screen completion and next decisions

Updated 2026-11-13. Active development plan: ignored `data/probes/windows-screen-mains-v1/plan.json` on Ganant's original Windows PC. Snapshot: **68/768 cells, 66 successes, one timeout, one execution error; 700 unattempted cells remain**. The earlier 36-cell diagnostic plan is separate.

## 1. Complete the existing screen

- Verify stable mains power, existing packages, unchanged research source, available memory and disk. Do not generate another dataset or repeat recorded cells.
- Continue at most 32 new cells per batch, with power/disk sampling, the original supervisor timeout, host-memory check and owned-process cleanup. Save and analyze every outcome, including failures.
- The two reviewed outcome types are a contained timeout and Dask `KilledWorker` with clean cleanup. These can remain recorded while later cells proceed. Interruptions, unknown errors, cleanup leftovers, low disk, command failures or power loss stop the controller for inspection.
- The local controller supports the following command. It keeps Windows awake while active; creating `pause.requested` in the run directory stops at the next batch boundary. Recorded failures are never retried by this command.

```powershell
.\.venv-research\Scripts\python.exe data/probes/windows-screen-mains-v1/advance.py --until 768 --continue-reviewed-failures
```

Completion means all 768 planned identities have recorded outcomes, not that every job succeeded. Audit uniqueness, plan/source/data identity, cleanup and condition intervals. The historical timeout overlaps a power disconnection and must stay flagged. Failed or power-confounded groups cannot support a clean performance comparison.

The first 68 attempts averaged about 7.1 seconds of recorded lifecycle time. Extrapolating gives about 83 minutes for the remaining 700, before repeated audits/analysis or additional long timeouts. This is a rough planning estimate, not a deadline. Existing data is reused; temporary spill can increase working disk use.

## 2. Analyze the research question

For complete eligible groups, compare full execution rankings against uniform, uniform with scaled memory, and partition-tail with that same scaled memory. Report aligned, inverted and unresolved pairs, selected-configuration regret, all failures, spill and restarts. Keep condition-affected outcomes visible; do not silently exclude rows to improve a result. Two repeats and the current coupled patterns provide exploratory evidence only.

Decide whether uniform-probe errors exceed repeat noise, whether memory scaling already solves them, and whether the partition heuristic improves on the matched-memory baseline. Pressure alone does not prove better recommendations. Numerical ranking comparisons require the full candidate/repeat sets to succeed under the declared protocol; other groups stay unevaluable.

## 3. Choose a justified follow-up

If a useful gap remains, declare independent follow-up instances and additional repeats, separating input imbalance, key skew, size and seed. Specify the adaptive policy before evaluating it: what it observes, when it expands a probe, and how it chooses or abstains. If simple baselines solve the problem or the heuristic gives no repeatable benefit, report that result and revise the direction.

## 4. Evaluate a final method and write the findings

Freeze development, calibration (if needed) and untouched final workload groups. Charge total request cost: sample preparation, every paid probe and a fresh selected full execution. Compare against predeclared baselines, retain failures and report resource/time tradeoffs and limitations. Train a reliability model only if the design needs one and independent labelled data supports it. Finish reproducible artifacts and the paper, then obtain the integration decision before merging this research branch into main.

The original LightGBM advisor's prospective validation remains a separate task. This research screen does not retrain that model or validate its cost-saving claim.
