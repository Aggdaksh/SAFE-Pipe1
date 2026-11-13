# Resume SAFE-Pipe — 2026-11-13

Read **[the canonical project context](../context.md)** first. It contains the current goal, constraints, baseline history, verified research work and ordered next steps. This entry point replaces the obsolete October 26 session status; that version remains in Git history.

## Resume the current task

- Goal: develop and evaluate a defensible research-paper contribution, currently investigating partition-aware adaptive probing under memory pressure.
- Branch: `codex/partition-probe-research`. The implementation/handoff was published at `975b446`; later context-only commits may follow. Check current Git status before editing.
- Stage: Windows checks and 16-cell smoke passed. The first diagnostic plan has 36 successes. The second monitored plan is at 68/768: 66 successes, one power-confounded timeout, and one `KilledWorker` execution error in the next stable-power batch. The monitor stopped for inspection; cleanup completed. No adaptive controller, new model training or proven novelty yet. Keep the branch separate until integration is decided.
- Constraint: **large experiments and training on the other laptop only**. On this Mac continue design/code/docs and small checks. Do not resume the old partial Mac plans.

## Read next

1. [Progress ledger](../PROGRESS.md) — baseline versus research status.
2. [Research evidence](../reports/research_probe_v1/README.md) — successful checks, incomplete experiments, observed spill and evidence gaps.
3. [Research protocol](research/PROBE_PROTOCOL.md) — methods, closest prior work and interpretation limits.
4. [Windows handoff](research/WINDOWS_HANDOFF.md) — small verification, fresh plan, batches, resume and export.

Useful work before heavy execution: specify the follow-up hypotheses/metrics, proposed adaptive decisions and cost accounting, factor-separated ablations, and paper outline. These are preparation tasks; performance conclusions must wait for measurements.

The active ignored plan is `data/probes/windows-screen-mains-v1/plan.json` on Ganant's PC. Use the [Windows handoff](research/WINDOWS_HANDOFF.md) and [monitored checkpoint](../reports/research_probe_windows_mains_v1_partial/README.md); the live count may advance beyond that exported snapshot. The first 36-cell diagnostic plan stays intact. The original main-v1 study/model are separate.
