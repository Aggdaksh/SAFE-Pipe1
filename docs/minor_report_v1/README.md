# Minor B.Tech Project report assets — v1

Prepared 21 November 2026. This is a working writing/evidence pack, not a signed or department-formatted final submission.

## Open these first

- [Visual evidence book](index.html): 18 figures, captions, sources, implementation examples, chapter mapping and remaining inputs.
- [First eight-chapter prose draft](REPORT_DRAFT.md): introduction through conclusion, with measured results, caveats and an explicitly unfinished literature review.
- [Printable PDF evidence book](../../output/pdf/safe_pipe_minor_report_v1/SAFE_Pipe_Minor_Report_Evidence_v1.pdf).
- [Saved advisor output viewer](advisor_demo.html): presents actual inference output; it is not the finished product UI.

## Contents and provenance

| Location | Purpose |
| --- | --- |
| `figures/` | 18 high-resolution PNGs and 18 vector SVGs. SVG text stays editable; keep captions and scope statements with reused figures. |
| `tables/` | 13 compact CSV tables, including original runtimes, split membership, saved test predictions, Stage A/B, probe cost and terminated-worker comparisons. Missing values are not backfilled with zero. |
| `figure_register.json` | Figure titles, full captions, source paths and intended chapter/topic. |
| `verified_facts.json` | Recomputed key results and their distinct study/test denominators. |
| `source_manifest.json` | Exact source revisions and LF-normalized SHA-256 hashes. |
| `advisor_capture/` | Four real inference-only CLI outputs, complete stderr files and command/hash records. |
| `screenshots/` | Browser captures of the report cover and saved-output viewer. These are screenshots of generated report pages, not benchmark monitors or a claimed product UI. |
| `build_assets.py` | Read-only existing-evidence analysis and figure generation; captures inference only if a case has no saved output. |
| `build_book.py` | Builds the offline HTML evidence book and viewer from saved assets. |
| `render_book.py` | Isolated headless Chrome/Edge PDF export and screenshots; adds PDF page numbers with PyMuPDF. |
| `quality_report.json` | Final source/count/link/PDF checks and scope record. |

Original-advisor evidence is pinned to `caa8a8a919d7cf4822e1735c795d22c31b63dc71`; the tested implementation is `d6f906a`. Research evidence and the prior report-planning review are read from `edef1cdbba0d980bc1a359960d7339cc08d13d84`. Reading those Git objects did not merge or enable the research code. Full raw records, physical inputs, credentials and the seniors’ PDFs are not copied into this pack.

The original saved model/data/source hashes still match the Windows verification receipt. The 13.84% runtime MdAPE and 23.01% baseline MdAPE are recomputed from the 24 saved held-out rows; worker-termination comparisons are recomputed from the existing worker export. No training accuracy or training curve is invented.

## Reproduce or revise

Run from the repository root on Windows. The figure builder uses the **system Python**, with its already-installed matplotlib/numpy packages, keeping both project environments unchanged. Browser rendering also uses the already-installed PyMuPDF package and Chrome/Edge. No package installation is part of these scripts.

```powershell
python docs/minor_report_v1/build_assets.py
python docs/minor_report_v1/build_book.py
python docs/minor_report_v1/render_book.py
python docs/minor_report_v1/check_pack.py
```

The figure builder needs both pinned commits available locally. A checkout without the research Git objects must fetch `codex/partition-probe-research` before building; it does not need to switch branches. Source checks deliberately refuse to run against an altered original verified source/model/table. Review any intentional implementation change and create a new evidence version rather than bypassing those checks.

Existing saved advisor captures are reused on a rebuild. If a capture is missing, the builder invokes only `.venv/Scripts/python.exe -m safe_pipe.cli advise`; no executor or generator is called. The four case definitions are balanced/resource/fastest at 13.1 seconds and abstention at 0.01 seconds. New captures after source changes need their own version/provenance, not silent replacement of these outputs.

Rendering uses an isolated profile under ignored `reports/_scratch/minor_report_v1/`, never the user’s real browser profile. This Windows sandbox required permission to launch the headless browser normally; do not disable browser sandboxing. Scratch logs and intermediate PDF renders remain ignored. Rebuilds replace only this pack’s generated figures/HTML/PDF, not the original verification folder or experiment files.

Edit the prose draft directly. Edit chart definitions/captions in `build_assets.py` and page layout in `build_book.py`, then regenerate and visually inspect the results. New fresh-study evidence belongs in a new pack version. PDF final pagination and academic front matter remain future work after official instructions and team identities are confirmed.

## Scientific and execution boundaries

- Original measurements, research development replays and software checks stay separate.
- Latest software result: 143 passed, zero failed/errors/skipped; no new full-suite run was needed for these documentation-only changes.
- All displayed research measurements come from existing records; there were no new Dask jobs for this pack.
- No dataset generation, model training, new study preparation, probe admission, Stage C or main merge occurred.
- No external stock or AI-generated image stands in for scientific results. Diagrams are labelled schematics; graphs use saved measurements.
- Literature review, official formatting, academic identity/signature fields and final supervisor review are still pending. The new 96-cell validation study still awaits review and authorization.
