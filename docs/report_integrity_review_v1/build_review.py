"""Build the offline review from the saved read-only audit; no external calls."""
import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
a = json.loads((BASE / 'local_audit.json').read_text(encoding='utf-8'))
esc = html.escape
rows = ''.join(
    '<tr><td>' + esc(x['source']) + '</td><td>' +
    str(len(x.get('front_matter_exact_spans_at_least_12_words', []))) +
    '</td><td>' + str(len(x.get('technical_chapters_exact_spans_at_least_12_words', []))) + '</td></tr>'
    for x in a['local_comparisons'])

page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAFE-Pipe | Similarity, AI writing and report review</title>
<style>
:root{--ink:#16283b;--muted:#526579;--blue:#125d99;--paper:#f3f6fa;--line:#d7e0e9;--amber:#fff1d8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 system-ui,Segoe UI,sans-serif}
header{background:#142d47;color:white;padding:64px max(24px,calc((100vw - 1060px)/2)) 42px}header p{color:#d0dfed;max-width:820px}
main{max-width:1108px;margin:auto;padding:28px 24px 70px}h1{font-size:clamp(30px,5vw,48px);line-height:1.16;margin:12px 0 20px}h2{font-size:28px;line-height:1.25;margin:0 0 18px}h3{font-size:20px;margin:18px 0 8px}
.eyebrow{letter-spacing:.13em;font-size:13px;text-transform:uppercase}.section{background:white;border:1px solid var(--line);border-radius:14px;padding:30px;margin:24px 0}
.note{border-left:5px solid var(--blue);background:#edf5fc;padding:18px 22px;margin:20px 0}.pending{background:var(--amber);border-left-color:#b66b00}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.card{background:#f3f7fb;border:1px solid var(--line);padding:22px;border-radius:10px}.card h3{margin-top:0}
.flow{display:flex;gap:12px;align-items:stretch;margin:22px 0;flex-wrap:wrap}.step{flex:1;min-width:170px;padding:18px;background:#edf5fc;border-radius:9px;border-top:4px solid var(--blue)}.step b{display:block;margin-bottom:6px}
.metric{font-size:34px;font-weight:700;line-height:1.1;color:var(--blue)}.muted,small{color:var(--muted)}a{color:#07578f;text-underline-offset:3px}header a{color:#d7eeff}
table{border-collapse:collapse;width:100%;font-size:15px}td,th{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:13px 10px}th{background:#eef3f8}.table-wrap{overflow-x:auto}
code{font:14px Consolas,monospace;overflow-wrap:anywhere}li{margin:9px 0}details{border-top:1px solid var(--line);padding:15px 0}summary{font-weight:650;cursor:pointer}footer{font-size:14px;color:var(--muted)}
@media(max-width:700px){.grid{grid-template-columns:1fr}.section{padding:22px 18px}header{padding-top:38px}table{min-width:560px}}
@media print{body{background:white;font-size:11pt}header{background:white;color:black;padding:10px 0}header p{color:black}main{padding:0}.section{break-inside:auto;border:0;padding:18px 0;margin:0;border-top:1px solid #aaa}.card,.step{break-inside:avoid}a{color:black}details{display:block}summary{list-style:none}}
</style></head><body>
<header><div class="eyebrow">SAFE-Pipe · Minor BTech report · 22 November 2026</div>
<h1>Understand the checks.<br>Review the actual report.</h1>
<p>A practical guide to similarity, AI-writing detection, character myths, useful open-source tools and the checks we have actually completed.</p>
<p><strong>Current status:</strong> local review completed; official Turnitin similarity and AI-writing results are still unknown.</p></header>
<main>
<section class="section"><h2>1. What this review establishes</h2>
<p>You confirmed that your department applies both similarity and AI-writing limits. The exact percentages and the rules for exclusions, resubmission and permitted AI assistance have not been supplied. We therefore cannot declare the report ready against those limits.</p>
<p>Useful tools can improve source attribution, references, grammar and document hygiene. They cannot certify the result that your institution's Turnitin account will produce. Because AI assisted with drafting this report, a local character check cannot establish that its prose will be classified as human-written.</p>
<div class="note"><strong>Deliverable:</strong> this evidence-based review, a reproducible local audit and a tool shortlist. The original DOCX was preserved byte-for-byte. No external checker received the report, and no new plugin or dependency was installed.</div>
<p><a href="../../output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx">Open the actual DOCX</a> · <a href="local_audit.json">Open the machine-readable audit</a> · <a href="audit_report.py">Read the audit script</a></p>
</section>

<section class="section"><h2>2. Two different scores, two different questions</h2>
<div class="grid"><article class="card"><h3>Similarity</h3><p>“How much text matches material in the comparison databases?”</p><p>Turnitin compares against sources including websites, publications and previously submitted student work. A match needs interpretation: a quotation, standard cover-page wording and an unattributed copied paragraph are different cases.</p><p><a href="https://guides.turnitin.com/hc/en-us/articles/23435833938701-Understanding-the-similarity-score">Official similarity explanation</a></p></article>
<article class="card"><h3>AI writing</h3><p>“How much qualifying prose does the model classify as likely AI-generated or AI-modified?”</p><p>This is independent of similarity. It is not the probability that a student cheated, and its denominator is qualifying long-form prose rather than every item on every page.</p><p><a href="https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report">Official AI-writing explanation</a></p></article></div>
<h3>A simple example</h3><p>A newly generated paragraph about Dask might match no existing source but still be classified as AI writing. Conversely, a paragraph written by a student can contain a correctly quoted passage that increases similarity. Improving one score does not establish the other.</p>
<p>Turnitin warns that its AI model can make mistakes and should not be the sole basis for adverse action. Its current report suppresses numerical results above zero and below 20%, showing an asterisk instead. <strong>That display rule is not a departmental allowance.</strong> <a href="https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report">Source</a></p>
</section>

<section class="section"><h2>3. What detection does—and what character cleaning does not do</h2>
<div class="flow" aria-label="Conceptual AI classification pipeline"><div class="step"><b>1 · Extract text</b>Read the submitted document's prose.</div><div class="step"><b>2 · Analyse passages</b>Evaluate overlapping text segments with a trained model.</div><div class="step"><b>3 · Combine results</b>Associate results with sentences and produce a report.</div></div>
<p>This is a conceptual description based on Turnitin's published explanation, not a reproduction of its proprietary implementation. The public description does not provide enough model weights, training data or version-specific details to reproduce your institution's result locally. <a href="https://in.turnitin.com/blog/ai-writing-detection-what-academic-leaders-need-to-know">Turnitin's mechanism overview</a></p>
<h3>Invisible characters are a separate issue</h3><p>Turnitin documents flags for hidden text and substituted look-alike characters. It also says it normalizes look-alikes during similarity scanning. Character substitution is therefore not a dependable way to interrupt matching; flags themselves still need human review. <a href="https://guides.turnitin.com/hc/en-us/articles/27397357797517-Integrity-Flags-in-the-new-enhanced-Similarity-Report">Official integrity-flags guidance</a></p>
<h3>A watermark is different from a classifier</h3><p>OpenAI's current provenance guidance describes textGrain watermarking in covered contexts, including EU ChatGPT and opt-in API settings. It changes statistical word-choice patterns rather than adding invisible characters, unusual punctuation or watermark-only tokens. Coverage varies; this review cannot tell whether our particular generated passages carry that signal. <a href="https://help.openai.com/en/articles/8912793-provenance-signals-in-content-processed-by-openai-tools">OpenAI provenance guidance</a></p>
<p>A statistical watermark detector looks for an embedded signal. A third-party classifier infers authorship from patterns in text. They are different mechanisms. The sources reviewed here do not establish that Turnitin uses OpenAI's watermark detector or keys.</p>
<div class="note">Removing an em dash, changing smart quotes or saving a DOCX as plain text does not establish that AI authorship has disappeared. Preserve valid equations, names and technical notation.</div>
</section>

<section class="section"><h2>4. What we checked in our SAFE-Pipe report</h2>
<p>The audited file is <code>output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx</code>. Its SHA-256 remained:</p>
<p><code>__HASH__</code></p>
<div class="grid"><article class="card"><div class="metric">0 found</div><h3>Selected character artifacts</h3><p>No checked zero-width/bidirectional characters or Cyrillic characters in the main document's Word text nodes. This is a selected-character check, not exhaustive document forensics.</p></article>
<article class="card"><div class="metric">55</div><h3>Normal navigation results</h3><p>The nonempty <code>webHidden</code> text runs were numeric page references in contents, figure and table lists. No unexpected non-navigation text was found in that set; no nonempty directly hidden <code>vanish</code> runs were found.</p></article></div>
<p>Word uses <code>webHidden</code> for some navigation formatting. Finding that XML property alone would have been misleading. We checked the text and paragraph styles instead of treating every occurrence as concealed writing.</p>
<h3>Local comparison with the two supplied senior reports</h3>
<p>We compared __TOKENS__ normalized word tokens from the eight technical chapters with extracted text from both PDFs. The comparison looked for exact contiguous matches of at least 12 words after case and punctuation normalization.</p>
<div class="table-wrap"><table><thead><tr><th>Senior sample</th><th>Front-matter matching spans</th><th>Technical-chapter matching spans ≥12 words</th></tr></thead><tbody>__ROWS__</tbody></table></div>
<p>The front-matter matches are institutional or degree wording, 12–16 words long. No qualifying technical-chapter match was found. This does not measure shorter reuse, paraphrasing, image text, mathematical elements, appendices or sources outside those two PDFs.</p>
<div class="note pending"><strong>No overall similarity percentage was calculated.</strong> “No exact match of 12 words or more in this small local corpus” is not “0% Turnitin similarity,” “plagiarism-free” or an AI-writing result.</div>
<p>The bibliography contains seven numbered entries. Their existence is not a claim-by-claim audit. Every borrowed idea, definition, diagram adaptation and literature claim still needs an appropriate source and accurate attribution. <a href="local_audit.json">Full scope, counts, source hashes and limitations</a></p>
</section>

<section class="section"><h2>5. Tools that can actually help</h2>
<p>The table separates what a tool does from what it cannot establish. These are research findings, not a record of installation or a security audit.</p>
<div class="table-wrap"><table><thead><tr><th>Tool / repository</th><th>Useful purpose</th><th>Limit for our report</th></tr></thead><tbody>
<tr><td><a href="https://github.com/zotero/zotero">Zotero</a><br><a href="https://www.zotero.org/support/word_processor_integration">Official Word integration</a></td><td>Manage verified source records and insert citations/bibliographies into Word.</td><td>Does not establish that a source supports a particular sentence, or lower an AI score by itself. Most directly useful for maintaining our references.</td></tr>
<tr><td><a href="https://github.com/languagetool-org/languagetool">LanguageTool</a></td><td>Grammar and style checks; a local server is possible.</td><td>Not a Turnitin replica or detector bypass. Check deployment/privacy before sending unpublished text to a hosted service.</td></tr>
<tr><td><a href="https://github.com/JonathanReeve/text-matcher">text-matcher</a></td><td>Compare supplied texts for overlapping passages.</td><td>Has no access to Turnitin's full corpus. Compatibility with this PC's Python has not been tested. Our saved audit uses its own small exact-match routine; it did not run this package.</td></tr>
<tr><td><a href="https://github.com/rspeer/python-ftfy">ftfy</a></td><td>Repair genuine Unicode/encoding corruption.</td><td>Does not remove statistical AI watermarks or establish authorship. Our audit does not reveal a character-cleaning requirement.</td></tr>
<tr><td><a href="https://github.com/grobidOrg/grobid">GROBID</a></td><td>Extract structured metadata/references from scholarly PDFs.</td><td>More infrastructure than we need for seven references; extraction does not verify a claim's truth.</td></tr>
<tr><td>Scite, available through plugin discovery</td><td>Find literature and inspect how papers are cited.</td><td>Not installed/connected or used in this review. Citation context still needs reading. It is not a similarity/AI pass certificate.</td></tr>
</tbody></table></div>
<h3>Can a GitHub repository become a ChatGPT plugin?</h3><p>Sometimes, with the appropriate integration. A repository is not automatically an installable ChatGPT app. MCP servers also require a supported connection, deployment, permissions and account/workspace configuration. <a href="https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-apps-in-chatgpt-beta">Official custom-app/MCP guidance</a></p>
<p><a href="https://github.com/virtualarchitectures/Local-Zotero-MCP">Local-Zotero-MCP</a> is one community integration candidate. It was not installed or security-reviewed. Keeping Zotero's database local does not mean that text returned to a cloud AI assistant stays offline.</p>
<p>The available plugin-directory search returned no Turnitin match. That is a bounded search result, not proof that no integration exists anywhere. No connected Turnitin account or institutional scan was available for this review.</p>
</section>

<section class="section"><h2>6. What the research can and cannot tell us</h2>
<p>Open detector research is useful for understanding mechanisms and limitations. It cannot predict a current proprietary score reliably:</p>
<ul><li><a href="https://github.com/ahans30/Binoculars">Binoculars</a> is a research detector using paired language-model scores. Its published model/threshold setup is not Turnitin's implementation. We did not download or run its large models.</li>
<li><a href="https://github.com/google-deepmind/synthid-text">SynthID Text</a> is a reference watermarking/detection project. It is a different research system, not a universal detector for arbitrary ChatGPT text.</li>
<li><a href="https://arxiv.org/abs/2304.02819">Liang et al. (2023)</a> studied detector bias against non-native English writing. That is evidence about the systems/settings tested then; it does not establish today's Turnitin false-positive rate.</li></ul>
<p>Do not treat a low score from a free checker as a prediction of Turnitin's output, or a high one as conclusive evidence of misconduct. Different systems use different models, text segmentation, thresholds and supported inputs.</p>
</section>

<section class="section"><h2>7. A practical route for our team</h2>
<ol><li><strong>Get the actual department rules.</strong> Record both cutoffs, permitted AI assistance, required disclosure and the handling of references, quotations and standard front matter. No current Minor BTech threshold was verified in this review; older postgraduate rules should not be substituted.</li>
<li><strong>Review the report chapter by chapter.</strong> Each student should explain the problem, inputs, model, decisions, studies, results and limitations without reading generated prose. Where the explanation is unclear, return to the source evidence and rebuild the section in the student's own informed account. This is an authorship and understanding step, not a promised detector outcome.</li>
<li><strong>Trace technical statements.</strong> Separate our original 96-run advisor study, later Stage A/B research and the 143-test software checkpoint. Tests passed is not runtime-model accuracy; a historical replay is not fresh independent validation. Use the repository's pinned evidence and preserve the actual denominators.</li>
<li><strong>Complete source attribution.</strong> Check each literature claim against the cited paper, quote exact wording when needed, and attribute adapted figures. A citation does not permit copying an entire passage without quotation, and rewording a borrowed idea does not remove its attribution requirement.</li>
<li><strong>Keep provenance.</strong> Retain Git revisions, raw evidence, source notes and genuine student drafts. Record AI assistance accurately according to the department's rules. Preserve the current DOCX before manual editing or regeneration.</li>
<li><strong>Request an authorized institutional draft check.</strong> Ask the guide or administrator whether an approved non-repository draft setting is available. Confirm storage rules before uploading: repository-stored earlier drafts can create self-matches. Review the similarity matches and the separate AI-writing report together with the applicable rules.</li>
<li><strong>Address actual findings.</strong> Correct unattributed reuse or unsupported claims; discuss disputed AI flags with the guide using drafts and project evidence. Repeat an approved scan only as the institution allows. We cannot guarantee that revisions will produce a particular AI score.</li></ol>
<p><a href="https://guides.turnitin.com/hc/en-us/articles/23713493434253-Understanding-the-similarity-score-for-students">Turnitin guidance on interpretation and prior-submission matches</a></p>
<div class="note pending">Remaining external checkpoint: the institution's two actual reports and exact acceptance rules. This local review is complete within its stated scope; acceptance remains unassessed.</div>
</section>

<section class="section"><h2>8. Reproduce and hand off</h2>
<p>From the repository root, using a Python installation with PyMuPDF already present:</p>
<p><code>python docs/report_integrity_review_v1/audit_report.py</code><br><code>python docs/report_integrity_review_v1/build_review.py</code></p>
<p>The first command reads the existing report and the two senior PDFs in the parent directory and updates only its own JSON output. It asserts that all eight chapters and a nontrivial text corpus were identified, and checks that the DOCX hash is unchanged. It reports missing sample files explicitly. The second command builds this offline page from that JSON. Neither command calls Turnitin or installs anything.</p>
<p>Scope limits: character checks cover selected code points and direct run properties in the main document XML; they do not exhaustively examine inherited formatting, white-on-white text, every document part or statistical watermarks. The text-overlap comparison excludes references, appendices, headers/footers, math-only elements and image text. There was no web-wide text search or claim-by-claim bibliography verification.</p>
<footer>Prepared for SAFE-Pipe's team on 22 November 2026. Links identify the vendor documentation, official repositories and research sources supporting this review. Product behaviour and tool compatibility can change. Original model/data and experiment gates were preserved; no main merge was performed.</footer>
</section></main></body></html>'''
page = page.replace('__HASH__', esc(a['report_sha256'])).replace('__ROWS__', rows).replace('__TOKENS__', str(a['comparison_scope']['technical_word_tokens']))
(BASE / 'index.html').write_text(page, encoding='utf-8')
print('Wrote', BASE / 'index.html')
