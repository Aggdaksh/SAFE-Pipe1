# Resume SAFE-Pipe — 2026-11-15

Read **[the canonical project context](../context.md)** first. It contains the current goal, constraints, baseline history, verified research work and ordered next steps. This entry point replaces the obsolete October 26 session status; that version remains in Git history.

## Resume the current task

- Goal: develop and evaluate a defensible research-paper contribution, currently investigating partition-aware adaptive probing under memory pressure.
- Branch: `codex/partition-probe-research`. The implementation/handoff was published at `975b446`; later context-only commits may follow. Check current Git status before editing.
- Stage: **Windows screen and Stage A complete:** the earlier screen has 768 retained attempts; Stage A has 48 (41 success, seven execution errors with nanny memory-termination evidence). Audit passed with zero cleanup survivors. Stage A interpretation is next; no Stage B, adaptive controller, new model or proven novelty yet. Keep the branch separate until integration is decided.
- Constraint: **all execution tests, dataset generation, experiments and training on Windows only**. This Mac is for code/docs and static checks. Do not resume the old partial Mac plans.

## Read next

1. [Progress ledger](../PROGRESS.md) — baseline versus research status.
2. [Research evidence](../reports/research_probe_v1/README.md) — successful checks, incomplete experiments, observed spill and evidence gaps.
3. [Research protocol](research/PROBE_PROTOCOL.md) — methods, closest prior work and interpretation limits.
4. [New Stage A Windows handoff](research/STAGE_A_WINDOWS.md) — targeted validation, fresh plan, batches, review and export. Supersedes historical execution instructions.

The deep post-hoc analysis, [staged follow-up plan](research/POST_SCREEN_PLAN.md), instrumentation code and 48-attempt Stage A specification are prepared. Read the [review](../reports/research_screen_review_20261114/README.md): fixed baselines are strong, full-scale reliability is not captured by successful small probes, and eight-probe overhead dominates these short jobs. **Windows checks and Stage A are now complete: 54 targeted tests passed; 48/48 attempts retained, with 41 success and seven errors carrying nanny memory-termination evidence.** Read the [results and audit](../reports/research_stage_a_windows_v1/README.md). No power flags or cleanup survivors; no later stage has started. The larger 432-attempt maximum is conditional, not scheduled. No new execution tests, training or pressure experiments were run on the Mac for this update.

The completed ignored plan is `data/probes/windows-screen-mains-v1/plan.json` on Ganant's PC. No benchmark is active. Read the [completed evidence and audit](../reports/research_probe_windows_mains_v1_complete/README.md) and [next research decisions](research/NEXT_STEPS.md). Earlier partial exports and diagnostic plans remain historical; the original main-v1 study/model are separate.
