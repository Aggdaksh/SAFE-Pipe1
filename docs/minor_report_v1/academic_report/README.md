# DTU Minor BTech Project report

**Prepared:** 22 November 2026. The deliverable is the actual academic report, distinct from the earlier figure evidence book.

[Open the editable Word report](../../../output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx).

The current native Word rendering has 36 physical pages: an unnumbered cover, eight Roman-numbered front-matter pages, and 27 Arabic-numbered pages of chapters, references and appendices. There are eight chapters, 14 figures, nine native tables and four editable Word equations. Pictures are embedded; the document does not depend on external image files to open.

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

The original 96-run model results, separate research development findings and software verification are distinguished. The original 78 source/evidence hashes remain unchanged. No fresh 96-cell study, dataset generation, training, Stage C, enabled probe admission or main merge was performed for document production. Signatures, supervisor approval and independent prospective results are not fabricated.
