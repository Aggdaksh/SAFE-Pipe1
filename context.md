# SAFE-Pipe project context

**Updated:** 2026-11-22. Read this file first when working from another PC.

## Active work: original-advisor completion

The user authorized implementing the completion plan on **one separate branch**, with merging deferred. This worktree uses **`codex/main-advisor-completion`**, based on `main` at `504f005`. Keep the research branch `codex/partition-probe-research` separate. The full release sequence and acceptance criteria are in [`docs/MAIN_COMPLETION_PLAN.md`](docs/MAIN_COMPLETION_PLAN.md).

Current deliverable implemented: a frozen prospective-study package, append-only attempt recording, fresh-results evaluator and Windows verification handoff. **Windows software verification passed on 2026-11-21 at implementation `d6f906a`: 143 passed, 0 failed, 0 errors, 0 skipped (36.89 s)** in the existing original-advisor `.venv` (Python 3.14.6). `pip check` passed; no dependencies were installed/upgraded and no implementation fixes were needed. The full suite included tiny Dask integration fixtures. Exact output, environment and 78 source/evidence hashes are in [`reports/main_validation_windows_checks_v1/`](reports/main_validation_windows_checks_v1/).

**Current stop point: evidence review.** The fresh 96-cell study has not been prepared or started. No original dataset was regenerated and no model was trained. The original model/curated-file byte hashes and original dataset size/mtime inventory were unchanged across verification; this inventory check is not a fresh full-dataset content-hash validation. Keep the receipt unchanged. Wait for the user's review before following the preparation/collection steps in [`docs/WINDOWS_MAIN_VALIDATION.md`](docs/WINDOWS_MAIN_VALIDATION.md).

**Execution constraint:** all project tests, Dask jobs, dataset generation and training belong on Windows. This Mac is for code/docs/review and static syntax checks only. Historical Mac-test descriptions below are not current authorization to run tests here.

After evidence review: bind saved advice to exact dataset execution, implement the small local interface and finish delivery. Broader profile support requires a separate versioned model/data design. Research-paper novelty remains a separate objective; none is established by this validation infrastructure.

## Purpose and scope

SAFE-Pipe recommends a configuration from eight declared local Dask configurations under an engine deadline, or abstains. The preferred `advise` command balances predicted speed and configured resource-time. Project-I measured four synthetic workload profiles on one Windows PC with worker memory caps of 1 GB and 2 GB: four families × eight configs × three repeats = 96 runs. LightGBM, upper estimates, support checks, baselines, and reports use that frozen run table. No general safety guarantee or multi-node result is established.

## Machines and Git branches

| Machine | Role |
| --- | --- |
| MacBook M3, 8 GB | Earlier coding, tiny pandas jobs, docs, unit tests |
| Windows 11 PC, 31.4 GiB physical RAM | User-selected physical Dask experiment host (ADR-005) |

The original 16 GB plan is a conservative sizing reference. The actual host has 32 GB marketed RAM; **worker caps and the eight-config grid stay unchanged**. The earlier Mac, Windows and advisor work is included in `main` after a 2026-10-28 fast-forward merge. Their original branches remain as checkpoints. For this completion task use `codex/main-advisor-completion`; use the research branch only for that separate study. Generated Parquet, JSONL runs, validation study directories and `.venv` are gitignored.

## Verified implementation

- Schemas, optimizer, eight-config grid, JSONL store, tiny four-family Parquet generators, pandas collector, and 96-cell planner came from the Mac branch.
- Windows `.venv` has `.[dev,dask,ml]` installed under Python 3.14.6. The merged `main` suite has **79 passing tests** on this PC, including tiny Dask executions, advisor regressions and the model-loading compatibility checks.
- T0 passed on the selected Windows PC: one 512 MB Dask worker returned the expected sum. See [`reports/t0.md`](reports/t0.md).
- T0b pilot compared 1 GB and 2 GB workers on two scan sizes and one sort size. The 136 MB sort took 10.58 s at 1 GB versus 4.53 s at 2 GB; both succeeded. See [`reports/t0b.md`](reports/t0b.md). No spill or OOM has been confirmed.
- Dask execution and one-cell collection are implemented; the scored matrix is complete (96 jobs below).
- Four `main-v1` datasets (175–198 MB) are generated, fingerprinted, and ignored by Git. The committed index is `configs/datasets_main_v1.json`.
- Twelve 2 GB SLA pilot runs succeeded. Deadlines and the randomized 96-cell order were frozen in `configs/` before scored collection. See `reports/matrix_preparation.md`.
- All 96 Dask cells were measured and audited: 96 successes, zero SLA misses. The curated CSV is committed at `data/curated/runs.csv`; raw JSONL and Parquet remain local.
- Grouped LightGBM plus conformal, a conservative rule-based OOD gate, fitted CLI recommendation, descriptive same-table baselines, and a feature-contribution figure are implemented. See `reports/runtime_model.md`, `reports/policy.md`, and `reports/shap.md`.
- New `advise` policy defaults to balanced speed/resources, with hard upper-runtime deadlines, optional budgets, exact frozen descriptors, bound grid/artifact checks and per-candidate comparisons. It reuses the model without training. See `docs/CONFIG_SELECTION.md` and `reports/advisor_v1/`.

## Original project checkpoint

The balanced selection implementation and the original Windows study are now merged into `main` and published. The technical results draft and separate tiny live Dask demo are complete. Remaining experimental work is prospective evaluation on the original Windows host; broader profiles need new data and a revised model/support policy. See `docs/INDEPENDENT_VALIDATION.md`. Formal submission remains pending. Optional TabPFN remains unrun; no failure classifier is supported because all 96 measured jobs succeeded.

## Design rules

- Use pre-run features only for inference. A job's actual runtime, memory, status, and spill cannot enter its prediction vector.
- Optimize the declared balanced dimensionless score using point runtime; test deadlines against the frozen upper estimate. Use explicit hard checks and abstain when none pass. Preserve historical cost/model features for old report reproduction.
- Keep memory caps at 1 GB and 2 GB despite the larger host. State that results come from a single Windows PC with induced worker caps.
- Failure handling stays deterministic until enough correctly labeled independent failure data supports training and held-out evaluation. A fixed number of positives alone does not establish classifier quality.
- Every reported number must identify its source study. Keep original measurements, fresh validation and research results separate. No Glue, 176-run, or unmeasured improvement claims.

## Documents

**Preferred learning-guide edition, 2026-11-23:** the user prefers English explanations followed by short Hinglish examples/recaps. `output/pdf/SAFE_Pipe_PPT_English_with_Hinglish_Guide.pdf` is the current 55-page study guide, retaining the eleven original slides and full technical detail. Editable content/build/QA are in `docs/ppt_english_guide_v2/`. The earlier Hinglish guide remains unchanged. This language revision adds no experiments or updated performance claims.

**PPT Hinglish companion, 2026-11-23:** `output/pdf/SAFE_Pipe_PPT_Hinglish_Step_by_Step_Guide.pdf` explains all eleven pages of the user's new presentation in a separate 55-page Roman Hinglish PDF. Original slides are unchanged; typed lessons cover the full project, four-method probe distinction, model/error math, memory evidence, cost and current limits. Editable content, pinned evidence links, builder and QA receipts are under `docs/ppt_hinglish_guide_v1/`. This is not a report/PPT edit or new experiment. Existing user DOCX modifications/deletion remain untouched.

**Current report after audit fixes, 2026-11-22:** `output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Evidence_Reviewed.docx` supersedes the earlier reviewed copy without overwriting the document open in Word. It clarifies statistical assumptions, exact training settings and limits, gives direct artifact references, and preserves earlier editorial changes. Rebuild with `docs/report_integrity_review_v1/build_evidence_report.ps1` using new output/QA paths; see the academic-report README. Its base is the hashed Word template at `297c0a4`, so the earlier revision chain is no longer required. The code change is explanatory only: `safe_pipe/models/runtime.py` no longer asserts independent cells. Historical verification hashes are checked at their pinned revision; 77 of 78 still match the current tree, and the single difference has an unchanged executable AST. Never rewrite the old receipt to make that difference disappear.

**Earlier fourteen-principle audit, 2026-11-22:** `docs/report_integrity_review_v1/principles_audit.html` preserves the read-only review and scoped gaps, with an implemented-follow-up note. Numerical claims and pinned hashes checked out. The documentation corrections identified there are applied in the current edition above; missing scientific evidence remains a limitation. The audit itself made no DOCX changes and was not whole-codebase certification or a new experiment.

**Friend review corrections, 2026-11-22:** The reviewed DOCX now includes the verified Figure 4 all-eight-eligible explanation and the requested declaration, certificate, acknowledgement and abstract edits. See `docs/report_integrity_review_v1/editorial_corrections.json`; apply these after the earlier revision plan when reproducing from the historical original. The original report remains preserved.

**Reviewed report copy, 2026-11-22:** `output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx` preserves the original and makes 13 targeted paragraph edits plus an AI-assistance disclosure. It remains 36 pages with 15 images, nine tables and four equations. Changes improve attribution and interpretation; no Turnitin score or pass probability is claimed. The user reports maximum 20% similarity and 20% AI writing. See `docs/report_integrity_review_v1/review_changes.html`, `revision_plan.json` and `revision_receipt.json`. Team understanding/source review and an institutional scan remain necessary. This revision is a separate native Word edit; rebuilding the older production content will not include these edits unless the revision plan is reapplied.

**Report integrity review, 2026-11-22:** [`docs/report_integrity_review_v1/index.html`](docs/report_integrity_review_v1/index.html) explains the separate Turnitin similarity/AI checks, current vendor guidance, useful tools and a practical authorship/citation workflow. The user confirmed both limits apply, and subsequently stated a maximum of 20% for each; official wording and scan settings remain unconfirmed. A read-only DOCX inspection and exact >=12-word comparison with the two supplied senior PDFs are saved in `local_audit.json`, with reproducible scripts. Only institutional front-matter spans matched; no qualifying technical-chapter spans matched in that bounded corpus. This is not a Turnitin percentage or an AI-authorship determination. The DOCX SHA-256 stayed `8df622f1c106665459e34cd72d060a1f1350f228e3a45f1d011e2a0370f62a1b`. No report upload, plugin/dependency installation, detector bypass or report rewrite occurred. Official institutional scans and operational department rules remain outstanding; do not infer submission clearance.

**Actual academic report, 2026-11-22:** [`output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx`](output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx) is the 36-page DTU-style Minor BTech report, with native text/tables/equations and embedded figures. It includes the DTU logo, the user's confirmed students/roll numbers and B.Tech VII Semester 2026-2027, and guide Prof. Dinesh Kumar Vishwakarma, Head of Department, IT, DTU. Declaration/certificate date and signature fields are blank. The report has eight chapters, seven references, 14 figures and nine tables. Native Word renders were reviewed; structural/provenance checks are in [`docs/minor_report_v1/academic_report/`](docs/minor_report_v1/academic_report/). Keep user edits to this DOCX; do not overwrite it with a rebuild without preserving them. No experiment gate was opened.

**Report production, 2026-11-21:** the Minor B.Tech Project writing pack is in [`docs/minor_report_v1/`](docs/minor_report_v1/): 18 PNG/SVG figures, 13 CSV tables, source/hash manifest, four inference-only CLI captures, an offline HTML evidence book, screenshots and the first eight-chapter prose draft. The PDF is under `output/pdf/safe_pipe_minor_report_v1/`. Existing evidence was read from pinned main-advisor and research commits; no research implementation was merged. Official front matter, checked literature and final formatting remain pending. This report work does not authorize fresh-study preparation or collection; the software-verification review gate above remains in force.

[`PROGRESS.md`](PROGRESS.md) is the status ledger; [`docs/MICROPLAN.md`](docs/MICROPLAN.md) has task cards; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) defines component contracts; [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) lists acceptance criteria; [`docs/PLAN_16GB.md`](docs/PLAN_16GB.md) is the conservative six-week schedule. ADR-005 records the actual host change.
