# SAFE-Pipe PPT: Roman Hinglish study companion

Prepared 23 November 2026 for the user's `BTP_new_PPT.pdf` (11 slides, deck dated 22 November). This is a separate learning guide, not an edit to the partner's PPT or academic report.

Deliverable: [55-page PDF](../../output/pdf/SAFE_Pipe_PPT_Hinglish_Step_by_Step_Guide.pdf).

The eleven original PDF pages are inserted intact at their original landscape dimensions. Each is followed by two to four portrait pages of searchable Roman Hinglish explanation. The guide has approximately 9,200 words of lesson notes, a linked reading map, bookmarks, worked examples, a revision number map, viva answers, a speaking script and a clickable evidence-file map.

## Evidence and interpretation

- Original-advisor evidence: `caa8a8a919d7cf4822e1735c795d22c31b63dc71`.
- Research evidence: `edef1cdbba0d980bc1a359960d7339cc08d13d84`.
- Current status/comment clarification: `8179c0737624560351fa4d5ca5a23a8f767329ff`.
- Source deck SHA-256: `50df261b72fee9818e6bf39945155098118750a13670e638a7dda19d4b666f70`.

Source IDs in the lesson footers resolve to the appendix links. `build_receipt.json` records each repository source's pinned revision and LF-normalized SHA-256, the source/output PDF hashes, and page map. Official Dask and LightGBM docs supply definitions, not project performance evidence.

The guide distinguishes four original workload profiles, eight worker configurations and four early research methods (one full reference plus three actual probes). It keeps the original 96 runs, Stage A's 48 full attempts, Stage B's 96 probes, disabled future 48-attempt draft and pending fresh 96-run study separate. It explains actual feature/model contracts, test error versus accuracy, descriptive coverage, historical versus prospective outcomes, worker lifetimes, telemetry under-observation, memory-cap units and unmeasured overhead. The earlier 10.96-second quote is explicitly untraced; it is not substituted for the checked 10.37-second aggregate. The historical 6.78 GiB figure is prepared storage across two screen directories, not a new disk inventory.

## Rebuild

`content.py` contains the editable Roman Hinglish lessons. `build_guide.py` reads only the pinned Git objects and user-supplied source PDF, and writes a new guide plus receipt. It refuses an existing output PDF. It does not import project experiment/model code.

Dependencies: Python, ReportLab, PyMuPDF and Pillow; Windows Arial fonts. Existing system PyMuPDF/Pillow were used. ReportLab 5.1.0 was installed with `--no-deps` into ignored `reports/_scratch/ppt_hinglish_guide_v1/pdf_deps`; neither SAFE-Pipe virtual environment was changed. Windows sandbox ACLs prevented reading that installed package in the restricted process, so the reviewed document-only build ran with elevated tool permissions. Poppler was unavailable; PyMuPDF provided rendering and visual QA.

From repository root, using an interpreter that can read those dependencies:

```powershell
python docs/ppt_hinglish_guide_v1/build_guide.py --source 'C:/Users/Ganant Awasthi/Downloads/BTP_new_PPT.pdf' --out 'output/pdf/SAFE_Pipe_PPT_Hinglish_Rebuild.pdf'
```

The input deck is outside Git. Teammates need that exact deck, or can extract the eleven original slide pages from the delivered guide using the recorded page map. A modified deck needs a new content/evidence review. The receipt describes the most recent build; preserve it with its corresponding PDF when making a new edition.

`check_guide.py` verifies the canonical deliverable against the receipt, compares all eleven original slide pages pixel-for-pixel and text-for-text, checks bounds/glyphs/navigation and renders all 55 pages into ignored scratch storage. Adjust its output path for a differently named rebuild. It does not establish new research accuracy or rerun the software suites. Final page renders were visually reviewed, with final wording changes compared against the first reviewed draft.

No benchmarks, data generation, model training, validation preparation, probe admission, main merge or report DOCX edit occurred. Pre-existing local report modifications/deletion and unrelated files were preserved.
