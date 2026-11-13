# Resume SAFE-Pipe — 2026-11-13

Read **[the canonical project context](../context.md)** first. It contains the current goal, constraints, baseline history, verified research work and ordered next steps. This entry point replaces the obsolete October 26 session status; that version remains in Git history.

## Resume the current task

- Goal: develop and evaluate a defensible research-paper contribution, currently investigating partition-aware adaptive probing under memory pressure.
- Branch: `codex/partition-probe-research`. The implementation/handoff was published at `975b446`; later context-only commits may follow. Check current Git status before editing.
- Stage: Windows compatibility checks and 16-cell smoke passed; the prepared development screen is at 36/768 successful cells. No adaptive controller, new model training or proven novelty yet. Keep the research branch separate until the user decides on integration.
- Constraint: **large experiments and training on the other laptop only**. On this Mac continue design/code/docs and small checks. Do not resume the old partial Mac plans.

## Read next

1. [Progress ledger](../PROGRESS.md) — baseline versus research status.
2. [Research evidence](../reports/research_probe_v1/README.md) — successful checks, incomplete experiments, observed spill and evidence gaps.
3. [Research protocol](research/PROBE_PROTOCOL.md) — methods, closest prior work and interpretation limits.
4. [Windows handoff](research/WINDOWS_HANDOFF.md) — small verification, fresh plan, batches, resume and export.

Useful work before heavy execution: specify the follow-up hypotheses/metrics, proposed adaptive decisions and cost accounting, factor-separated ablations, and paper outline. These are preparation tasks; performance conclusions must wait for measurements.

The Windows research screen has started on Ganant's original experiment PC. Its ignored local plan is resumable there; use the [Windows handoff](research/WINDOWS_HANDOFF.md) and [36-cell checkpoint](../reports/research_probe_windows_v1_partial/README.md). The original 96-run study and model already exist on main and should not be recreated from the old October 26 instructions.
