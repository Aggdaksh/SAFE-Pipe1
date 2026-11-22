# DTU Minor BTech Project report

**Prepared:** 22 November 2026. The deliverable is the actual academic report, distinct from the earlier figure evidence book.

[Open the current evidence-reviewed Word report](../../../output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Evidence_Reviewed.docx).

## Current version and repeatable build

The current edition has 37 physical pages, 14 figures, nine native tables, four editable equations and 15 bibliography entries. Visual review found no clipped or overlapping content.

The `report-evidence-v2` edition supersedes the original and earlier `_Reviewed` file. It preserves the friend-review corrections and AI-assistance disclosure, qualifies calibration assumptions and model-choice evidence, adds the training seed/encoding and Windows compatibility issue, and supplies eight direct artifact references. Its authoritative source is `docs/report_integrity_review_v1/evidence_revision_plan.json` applied to the pinned, SHA-256-checked Word template from commit `297c0a4`. Earlier production scripts below describe historical versions; do not replay their edit chain for this edition.

The template is stored in Git, with embedded images, native equations and tables. This is a versioned-template build, not a fresh experiment or a claim that the entire document is generated from raw measurements. It requires Python 3 and Microsoft Word on Windows. The preparer uses Python's standard library; rendering uses native Word. No installation, data generation, training or Dask execution occurs.

From the repository root, choose new output paths to preserve existing edits:

```powershell
& ([scriptblock]::Create((Get-Content -LiteralPath 'docs/report_integrity_review_v1/build_evidence_report.ps1' -Raw))) `
  -OutputPath 'output/docx/SAFE_Pipe_Report_Rebuild_Check.docx' `
  -QaDirectory 'reports/_scratch/report_rebuild_check'
```

The script refuses existing output/QA paths, reads the exact template from local Git history, verifies its hash, applies paragraph/reference changes and updates Word fields before saving DOCX and a private QA PDF. Fetch the recorded revision if absent from a shallow clone; do not substitute a different template. Script-block invocation accommodates this PC's file-execution policy without changing it.

The deliverable was rebuilt independently into scratch storage. `evidence_revision_receipt.json` records text and rendered-page comparisons, structural checks and source identities. Word-produced DOCX byte hashes may differ because of metadata; the reproduction claim is identical text and rendered page pixels on this host. Cross-version Word/font rendering and a fresh-clone installation were not tested.

`verify_evidence_report.py` reproduces the local verification using the deliverable and scratch outputs. Its defaults identify this PC's retained files: final QA `reports/_scratch/report_evidence_v2_03`, isolated rebuild `reports/_scratch/report_evidence_rebuild_v2_03.docx` with PDF in the matching directory, and prior PDF `reports/_scratch/report_revision_v1/reviewed.pdf`. These ignored previews are not shipped in Git. On another machine, generate both builds first and supply `--qa`, `--docx`, `--rebuild-docx`, `--rebuild-pdf` and `--previous-pdf` for the corresponding local files. The previous PDF must be rendered from the pinned earlier report. Use `--help` for arguments and `--receipt` for a new receipt path; the committed receipt is not overwritten. Rasterization uses the existing PyMuPDF/Pillow installation. `prepare_evidence_plan.py` reconstructs the committed plan from the pinned prior report; it is a maintenance helper, not needed for a normal rebuild. Preserve manual edits before changing the plan/template.

## Evidence access and limits

Compact results and figure inputs are pinned in `docs/minor_report_v1/source_manifest.json`, across original-advisor revision `caa8a8a` and research revision `edef1cd`. These Git objects and the code support checking tables and generating visualizations. References [8]–[15] point directly to training, predictions, research summaries, worker export and verification artifacts.

Full Stage A/B records are local under ignored `data/probes/windows-stage-a-v1/` and `data/probes/windows-stage-b-v1/`. Both directories' `runs.jsonl` and `plan.json` hashes were rechecked against `edef1cd:reports/worker_memory_stage_a_b_v1/verification.json`. This does not re-audit every diagnostic or Parquet file. Teammates needing raw evidence must obtain the retained directories from the experiment host using the team's agreed file transfer and verify the recorded manifests. Compact exports are not raw backups. Credentials and virtual environments must not be included in the transfer.

The historical 143-test receipt stays unchanged. All 78 historical hashes were verified at their pinned revision; 77 still match working source, while `safe_pipe/models/runtime.py` has a clarified docstring. An AST comparison excluding docstrings confirms unchanged executable code. The old current-worktree hash check will flag this intentional change; do not alter the historical receipt to hide it. This revision does not assert a new suite result, experiment or statistical guarantee.

## Historical original edition

The original native Word rendering had 36 physical pages: an unnumbered cover, eight Roman-numbered front-matter pages, and 27 Arabic-numbered pages of chapters, references and appendices. It contained eight chapters, 14 figures, nine native tables and four editable Word equations. Pictures are embedded; the document does not depend on external image files to open.

The cover and front matter follow the user-supplied DTU senior report examples. The DTU seal is a rendered extraction of the logo region in the supplied Information Technology sample. The samples and source synopsis remain unmodified outside the repository. No unrelated senior-project prose, results, signatures or medical figures are copied.

The team order, roll numbers and semester/session follow the user's latest supplied details. The guide is Prof. Dinesh Kumar Vishwakarma, Head of Department, Department of Information Technology, DTU. Declaration and certificate signature/date lines are blank for real review and signing. The report is not represented as already approved or signed.

## Production files

- `report_content.json`: ordered prose, figures, tables, identities and references.
- `build_content.mjs`: assembles the report from the existing prose/evidence pack and adds the background/related-work chapter and checked primary-source references. Run its exported `build(repositoryRoot)` function in the managed Node environment.
- `build_word.ps1`: creates native Word content, sections, fields, captions, tables and embedded figures using installed Word 16.
- `mdape.omml.xml` and `polish_word.ps1`: preserve the MdAPE fraction as explicit native Word math, keep short tables together, tidy source/reference alignment and update navigation fields.
- `check_report.py`: checks DOCX integrity, captions, image embedding, equation structure, identities, numbering and the unchanged original source hashes; rasterizes the native Word preview for visual review.
- `word_build_result.json`, `report_quality.json`: recorded production and structural checks.
- `format_contract.md`: the reference-derived layout and production boundaries.
- `references.json`: the seven numbered primary/project references used in the report.

The managed Python document runtime/loader and bundled renderer were unavailable in this session. Creation and preview export therefore used installed Microsoft Word through its native automation API, followed by PyMuPDF page rasterization. No package was installed in either project environment. Word's direct PDF save method was used after an export-method compatibility problem. QA previews and early attempts are retained only under ignored `reports/_scratch/minor_actual_report_v1/`; the deliverable is the DOCX above.

The PowerShell machine policy disables direct `.ps1` file invocation. The reviewed local code was run as an inline ScriptBlock without changing the machine execution policy. Native Word automation always starts a separate empty instance and closes only that instance. Existing user documents are not edited or closed.

For future content/layout revisions, rebuild the content, run the Word builder, apply the polish step, then rerun the checker and inspect the new native page renders. Use a new output/version if the user has edited the delivered DOCX. Do not overwrite user changes. In Word, update the contents/figure/table fields after editing with Select All and Update Fields.

## Evidence boundaries

The original 96-run model results, separate research development findings and software verification are distinguished. All 78 source/evidence hashes matched during original production; the later intentional docstring-only difference is documented above. No fresh 96-cell study, dataset generation, training, Stage C, enabled probe admission or main merge was performed for document production. Signatures, supervisor approval and independent prospective results are not fabricated.
