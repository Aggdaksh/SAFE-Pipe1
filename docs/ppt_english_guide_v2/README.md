# English explanations with short Hinglish examples

Prepared 23 November 2026 after the user clarified their learning preference: English first, with a brief Hinglish explanation/example for reinforcement.

Current deliverable: [55-page English-first PDF](../../output/pdf/SAFE_Pipe_PPT_English_with_Hinglish_Guide.pdf).

The original eleven slides remain intact. The 35 lesson/revision pages contain about 9,400 words, primarily English, with one short shaded Hinglish aid per lesson. Cover, navigation, speaking script and evidence-file walkthrough are also in English; the walkthrough has its own short Hinglish recap. The earlier fully Hinglish PDF is preserved byte-for-byte.

## Contents and boundaries

The revision retains the complete project narrative, worked score calculations, original model inputs and split, calibration/error interpretation, probe methods, Stage A/B and worker-memory findings, profiling economics, test checkpoints and future-work boundaries. It preserves the distinction between one full reference and three sample-probe methods. Illustrative examples remain separate from measurements. The source deck, partner PPT, report DOCX files, model and data were not modified.

Evidence remains pinned to original-advisor `caa8a8a`, research `edef1cd` and status/comment clarification `8179c07`. This is a language/layout revision, not a new experiment-status audit or a fresh benchmark. The source manifest and content/page map are in `build_receipt.json`.

## Build and check

- `content.py`: English lessons and their short Roman Hinglish examples/recaps.
- `build_guide.py`: this edition's PDF layout and pinned evidence reads; adapted from the retained first-edition builder to preserve that edition independently.
- `check_guide.py`: PDF bounds/glyph/navigation checks, pixel/text comparison against all original slides, previous-guide hash preservation and page renders.
- `build_receipt.json` and `quality_receipt.json`: hashes, source identities, structure and reviewed layout status.

The build uses the already installed isolated ReportLab package under ignored `reports/_scratch/ppt_hinglish_guide_v1/pdf_deps`, system PyMuPDF/Pillow and Windows Arial fonts. No new dependency was installed in this turn; neither research environment changed. Native PDF rendering and visual review use PyMuPDF because Poppler is unavailable. The document-only build used elevated tool permissions to read the isolated package's Windows ACL-protected directory.

```powershell
python docs/ppt_english_guide_v2/build_guide.py --source 'C:/Users/Ganant Awasthi/Downloads/BTP_new_PPT.pdf' --out 'output/pdf/SAFE_Pipe_English_Rebuild.pdf'
```

The builder refuses an existing output PDF. It needs the original deck and pinned Git history. Preserve the matching build receipt when creating another edition. The checker targets the canonical output above; adjust that path to check a differently named rebuild. Rerender and visually inspect after changing content; automated bounds checks alone do not establish layout quality.

All 55 output pages were visually inspected. The eleven source slides are pixel- and text-identical, all eleven contents links work, and the old Hinglish PDF retains SHA-256 `436526b128a3755080ce6e423d1ac7e4981fd379aeaed19f502ddb545e7f5c3d`. No benchmark, training, experiment preparation or main merge occurred. Existing user report modifications/deletion and unrelated work were left untouched.
