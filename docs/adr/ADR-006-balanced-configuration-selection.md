# ADR-006: Explained balanced configuration selection

- Date: 2026-10-27
- Status: Implemented; independent physical policy validation pending

## Decision

Add `safe-pipe advise` as the preferred selection interface. The user chose balanced speed and resource use. Default to an equal latency/resource-time score, with equal configured-thread and configured-memory shares inside the resource term. Normalize against fixed references; evaluate deadline upper estimates, workload support and resource budgets as independent hard constraints. Abstain if no candidate passes. Explain every candidate and provide whole-configuration model comparisons.

Reuse the existing runtime model and calibration without fitting or retuning weights on recorded outcomes. Bind support to audited main-v1 profiles and configuration definitions. Correct SI/IEC memory accounting only in the new score; preserve legacy fitted feature semantics. Keep the old recommendation path reproducible, except that a hard memory guard can no longer be bypassed by `failure_limit=1`.

## Rationale and consequences

The old `runtime × (nominal threads + nominal GB)` proxy mixes unnormalized units and hides preferences. The new formula makes the tradeoff explicit, keeps scores stable when alternatives are filtered, and follows the user's stated priority. Thread counts are configured concurrency, not dedicated vCPUs. Configured memory-time is not peak RAM or money.

Current evidence consists of four profiles and 96 successful runs on one Windows PC. No learned failure probability or broader workload generalization is established. The exact descriptor gate intentionally refuses changed profiles. A new model, feature contract and support policy require separate development and validation; they cannot be enabled by editing the existing index. Formula and CLI details: [configuration selection](../CONFIG_SELECTION.md).
