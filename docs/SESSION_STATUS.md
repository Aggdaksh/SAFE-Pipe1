# Resume SAFE-Pipe — 2026-11-16

Read **[the canonical project context](../context.md)** first. It contains the current goal, constraints, baseline history, verified research work and ordered next steps. This entry point replaces the obsolete October 26 session status; that version remains in Git history.

## Resume the current task

**Latest:** Stage B is complete on Windows: 74 targeted tests passed, 96/96 quiet successful probes, completion audit passed. Eight comparison groups gave false-reassurance candidates, and the six-probe replay did not improve on the simple metadata baseline. Read the [completed evidence](../reports/research_stage_b_windows_v1/README.md). No Stage C, training or main merge.

- Goal: develop and evaluate a defensible research-paper contribution, currently investigating partition-aware adaptive probing under memory pressure.
- Branch: `codex/partition-probe-research`. The implementation/handoff was published at `975b446`; later context-only commits may follow. Check current Git status before editing.
- Stage: screen, Stage A and Stage B are complete and archived. Stage B interpretation is next; no final adaptive controller or proven novelty. Keep the research branch separate until integration is decided.
- Constraint: **all execution tests, dataset generation, experiments and training on Windows only**. This Mac is for code/docs and static checks. Do not resume the old partial Mac plans.

## Read next

1. [Progress ledger](../PROGRESS.md) — baseline versus research status.
2. [Research evidence](../reports/research_probe_v1/README.md) — successful checks, incomplete experiments, observed spill and evidence gaps.
3. [Research protocol](research/PROBE_PROTOCOL.md) — methods, closest prior work and interpretation limits.
4. [Stage B Windows handoff](research/STAGE_B_WINDOWS.md) — new targeted validation, reuse of exact Stage A inputs, 96-probe plan, batches, audit and export.

The deep post-hoc analysis, [staged follow-up plan](research/POST_SCREEN_PLAN.md), instrumentation code and 48-attempt Stage A specification are prepared. Read the [review](../reports/research_screen_review_20261114/README.md): fixed baselines are strong, full-scale reliability is not captured by successful small probes, and eight-probe overhead dominates these short jobs. **Windows checks and Stage A are now complete: 54 targeted tests passed; 48/48 attempts retained, with 41 success and seven errors carrying nanny memory-termination evidence.** Read the [results and audit](../reports/research_stage_a_windows_v1/README.md). No power flags or cleanup survivors in Stage A; Stage B has since completed in a separate Windows session. The larger 432-attempt maximum is conditional, not scheduled. No new execution tests, training or pressure experiments were run on the Mac for this update.

The completed ignored plan is `data/probes/windows-screen-mains-v1/plan.json` on Ganant's PC. No benchmark is active. Read the [completed evidence and audit](../reports/research_probe_windows_mains_v1_complete/README.md) and [next research decisions](research/NEXT_STEPS.md). Earlier partial exports and diagnostic plans remain historical; the original main-v1 study/model are separate.
