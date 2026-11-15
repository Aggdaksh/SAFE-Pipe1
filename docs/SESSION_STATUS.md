# Resume SAFE-Pipe — 2026-11-15

Read **[the canonical project context](../context.md)** first. It contains the current goal, constraints, baseline history, verified research work and ordered next steps. This entry point replaces the obsolete October 26 session status; that version remains in Git history.

## Resume the current task

- Goal: develop and evaluate a defensible research-paper contribution, currently investigating partition-aware adaptive probing under memory pressure.
- Branch: `codex/partition-probe-research`. The implementation/handoff was published at `975b446`; later context-only commits may follow. Check current Git status before editing.
- Stage: **Windows development collection complete:** 768/768 attempts, 759 successes, one timeout and eight execution errors. Audit passed with zero cleanup survivors. Ten instances support descriptive comparisons; the partition heuristic has no established overall advantage. No adaptive controller, new model or proven novelty yet. Keep the branch separate until integration is decided.
- Constraint: **large experiments and training on the other laptop only**. On this Mac continue design/code/docs and small checks. Do not resume the old partial Mac plans.

## Read next

1. [Progress ledger](../PROGRESS.md) — baseline versus research status.
2. [Research evidence](../reports/research_probe_v1/README.md) — successful checks, incomplete experiments, observed spill and evidence gaps.
3. [Research protocol](research/PROBE_PROTOCOL.md) — methods, closest prior work and interpretation limits.
4. [Windows handoff](research/WINDOWS_HANDOFF.md) — small verification, fresh plan, batches, resume and export.

The deep post-hoc analysis and [staged follow-up proposal](research/POST_SCREEN_PLAN.md) are complete. Read the [review](../reports/research_screen_review_20261114/README.md): fixed baselines are strong, full-scale reliability is not captured by successful small probes, and eight-probe overhead dominates these short jobs. The next code task is persistent failure diagnostics and phase-cost accounting, followed by a frozen 48-attempt Stage A design. The larger 432-attempt maximum is conditional, not scheduled. No new training or pressure experiments were run on the Mac.

The completed ignored plan is `data/probes/windows-screen-mains-v1/plan.json` on Ganant's PC. No benchmark is active. Read the [completed evidence and audit](../reports/research_probe_windows_mains_v1_complete/README.md) and [next research decisions](research/NEXT_STEPS.md). Earlier partial exports and diagnostic plans remain historical; the original main-v1 study/model are separate.
