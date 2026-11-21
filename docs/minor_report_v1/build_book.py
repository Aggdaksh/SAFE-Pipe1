"""Assemble the offline report evidence book from the generated register."""
from pathlib import Path
import html
import json

HERE = Path(__file__).resolve().parent
figures = json.loads((HERE / "figure_register.json").read_text())
facts = json.loads((HERE / "verified_facts.json").read_text())
esc = html.escape
CSS = """
:root{--ink:#142b43;--muted:#516477;--teal:#087f8c;--blue:#2563a6;--line:#dae4ec}
*{box-sizing:border-box}body{margin:0;background:#e9eff4;color:var(--ink);font:16px/1.65 'Segoe UI',Arial,sans-serif}
nav{position:sticky;top:0;background:#142b43;color:white;padding:12px 30px;z-index:2;display:flex;gap:22px;align-items:center}
nav a{color:white;text-decoration:none;font-size:14px}nav strong{margin-right:auto}a{color:var(--blue)}
main{max-width:1120px;margin:30px auto}.sheet{background:white;border:1px solid var(--line);padding:48px 56px;margin:24px 0;border-radius:10px;box-shadow:0 8px 28px #142b4308}
.cover{background:linear-gradient(120deg,#102b43,#194c65);color:white;padding:65px 56px}.cover h1{font-size:65px;letter-spacing:-3px;margin:8px 0;line-height:1.05}.cover h2{font-size:26px;font-weight:400;color:#c5e7ed;line-height:1.4}
.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:12px;font-weight:700;color:var(--teal)}.cover .eyebrow{color:#83d7db}
h1,h2,h3{line-height:1.25}h2{font-size:30px;margin:10px 0 20px}h3{font-size:19px;margin-top:26px}p{margin:12px 0}.muted,.source{color:var(--muted);font-size:13px}.cover .muted{color:#c9dce6}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:26px 0}.card{padding:20px;background:#eef5f8;border-radius:8px}.card b{font-size:30px;display:block;line-height:1.2}.card span{font-size:13px;color:var(--muted)}
.notice{border-left:4px solid var(--teal);padding:14px 18px;background:#edf7f6;margin:20px 0}.warning{border-color:#c48a16;background:#fff7e7}
table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{background:#eef4f8;font-weight:600}
.toc{columns:2;column-gap:32px;font-size:14px}.toc a{display:block;margin-bottom:9px;break-inside:avoid}.figure img{width:100%;height:auto;display:block;margin:24px auto}.caption{font-size:15px}.source{overflow-wrap:anywhere;border-top:1px solid var(--line);padding-top:14px}.downloads a{display:inline-block;margin-right:16px;font-size:13px}.figure .number{font-size:13px;letter-spacing:2px;color:var(--teal);font-weight:bold}.figure h2{font-size:28px}
code{background:#edf2f6;border-radius:3px;padding:2px 5px;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#142b43;color:#e7f2f8;padding:20px;font-size:13px;border-radius:7px}li{margin:7px 0}.demo-title{font-size:42px!important}.tag{background:#d9eee9;color:#065d63;padding:3px 8px;border-radius:4px;font-size:12px}.tag.red{background:#f6dde0;color:#8d2635}
@page{size:A4;margin:17mm 16mm} @media print{body{background:white;font-size:10pt;line-height:1.5}nav,.downloads{display:none}main{max-width:none;margin:0}.sheet{border:0;border-radius:0;box-shadow:none;padding:0;margin:0;break-after:page;page-break-after:always;min-height:245mm}.sheet:last-child{break-after:auto;page-break-after:auto}.cover{background:#142b43!important;color:white!important;min-height:245mm;padding:22mm 16mm;print-color-adjust:exact;-webkit-print-color-adjust:exact}.cover h1{font-size:48pt}.cover h2{font-size:22pt}h2{font-size:22pt}.figure h2{font-size:21pt}.figure img{max-height:158mm;object-fit:contain;margin:8mm auto 6mm}.caption{font-size:10pt}.source{font-size:8pt}table{font-size:9pt}.cards{gap:8px}.card{padding:12px;print-color-adjust:exact}.card b{font-size:23pt}.toc{font-size:9pt}.notice{print-color-adjust:exact}a{color:inherit;text-decoration:none}}
"""


def page(content, cls="", ident=""):
    return f'<section class="sheet {cls}" id="{ident}">{content}</section>'


def document(title, body):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{CSS}</style></head><body>{body}</body></html>'


cover = page("""<div class="eyebrow">Minor B.Tech Project / working evidence book / v1</div>
<h1>SAFE-Pipe</h1><h2>A bounded advisor for choosing local Dask configurations under an engine deadline.</h2>
<p>Figures, measured results, worked examples and a clear account of what is still unproven.</p>
<div style="height:40px"></div><p>Prepared 21 November 2026</p>
<p class="muted">Original Windows study + separate research development + latest software verification</p>
<div style="height:35px"></div><p class="muted">This is the editable evidence pack for building the academic report. It is not a department-approved, signed or final submission.</p>
<p class="muted">Every quantitative figure has units, a sample count, a caveat and a source. No fresh benchmark or model training was needed to build this pack.</p>""", "cover", "start")

overview = page("""<div class="eyebrow">Start here</div><h2>What we can say today</h2>
<div class="cards"><div class="card"><b>96</b><span>Original physical runs<br>4 profiles x 8 settings x 3 repeats</span></div><div class="card"><b>13.84%</b><span>Held-out runtime MdAPE<br>24 rows / 8 family-setting groups</span></div><div class="card"><b>143 / 143</b><span>Latest main-advisor Windows tests<br>Zero failures, errors or skips</span></div></div>
<p>SAFE-Pipe estimates engine runtime for eight supported configurations. It checks the deadline, declared budgets and profile support, then recommends an eligible configuration or abstains. Its measured scope is the original four workload profiles on one Windows host.</p>
<table><tr><th>Evidence stream</th><th>What it establishes</th><th>What it does not establish</th></tr>
<tr><td>Original 96-run study</td><td>A fitted runtime predictor; descriptive comparisons on fixed synthetic profiles.</td><td>Accuracy on new workloads, learned failure risk or independent savings.</td></tr>
<tr><td>Research Stage A/B</td><td>Full-job memory pressure and limitations of small execution probes.</td><td>A beneficial online probe policy or a calibrated failure predictor.</td></tr>
<tr><td>Latest completion branch</td><td>Fresh-study recording/evaluation software passes the Windows suite.</td><td>Fresh measurements. The new 96-cell study is not prepared or started.</td></tr></table>
<div class="notice warning"><strong>Keep the denominators visible.</strong> 96 runs are not 96 independent workloads. 143 software tests are not 143 experiments. MdAPE is error, not “100 minus error” accuracy. The historical 34.1% cost difference is a same-table descriptive result.</div>
<p class="source">Pinned original-advisor evidence: caa8a8a; tested implementation: d6f906a. Pinned research evidence: edef1cd. Exact source paths and LF-normalized SHA-256 hashes are saved in source_manifest.json.</p>""", ident="overview")

contents = page('<div class="eyebrow">Figure atlas</div><h2>Choose a figure to explore</h2><p>Each figure is supplied as a high-resolution PNG and editable vector SVG. Captions are ready to adapt into the report.</p><div class="toc">' + ''.join(f'<a href="#{f["id"]}"><b>{f["id"].split("_")[0]}</b> &nbsp; {esc(f["title"])}</a>' for f in figures) + '</div><h3>How to use this pack</h3><ol><li>Read the first report prose draft in <code>REPORT_DRAFT.md</code>.</li><li>Use SVG in Word or a vector editor; use PNG where SVG is unsupported.</li><li>Keep the caption, timing scope, denominator and limitation with its figure.</li><li>Use the CSV tables to change presentation without changing evidence.</li><li>Put future study results in a new evidence version.</li></ol><p><a href="advisor_demo.html">Saved-advisor-output viewer</a> · <a href="REPORT_DRAFT.md">First prose draft</a></p>', ident="contents")
pages = [cover, overview, contents]
for f in figures:
    sources = '; '.join(f["sources"])
    pages.append(page(f'<div class="number">{esc(f["id"].split("_")[0])} / {esc(f["section"])}</div><h2>{esc(f["title"])}</h2><figure style="margin:0"><img src="figures/{f["id"]}.png" alt="{esc(f["title"])}"><figcaption class="caption">{esc(f["caption"])}</figcaption></figure><p class="source"><strong>Source:</strong> {esc(sources)}. Research sources are read from pinned Git objects; no research implementation was merged.</p><div class="downloads"><a href="figures/{f["id"]}.svg">Vector SVG</a><a href="figures/{f["id"]}.png">High-resolution PNG</a></div>', "figure", f["id"]))

captures = []
for case, label in [("sort_balanced", "Balanced"), ("sort_resource", "Resource"), ("sort_fastest", "Fastest"), ("sort_abstain", "Deadline too tight")]:
    data = json.loads((HERE / f"advisor_capture/{case}.json").read_text())
    captures.append((case, label, data))
demo_rows = ''.join(f'<tr><td>{label}</td><td>{esc(data["decision"]["action"])}</td><td>{esc(str(data["decision"].get("config_id") or "none"))}</td><td>{data["effective_deadline_seconds"]:g} s</td></tr>' for case, label, data in captures)
pages.append(page('<div class="eyebrow">Actual implementation output</div><h2>A compact advisor demonstration</h2><p>These examples were captured from the original Windows <code>.venv</code> using <code>safe_pipe.cli advise</code>. They load the saved model and perform inference only. No workload was executed.</p><table><tr><th>Preference</th><th>Action</th><th>Configuration</th><th>Effective deadline</th></tr>' + demo_rows + '</table><pre>.\\.venv\\Scripts\\python.exe -m safe_pipe.cli advise --family sort_merge --sla 13.1\n# Add --mode resource or --mode fastest\n# Use --sla 0.01 to demonstrate abstention</pre><div class="notice">A recommendation is a prediction-based choice. It is not a recorded fresh execution, measured saving, or guarantee for an arbitrary input.</div><p>Complete JSON output, stderr and commands are in <code>advisor_capture/</code>. The companion HTML page presents this saved output; it is an evidence viewer, not a completed product UI.</p><p class="source">Source: advisor_capture/commands.json and the four captured JSON documents. Original model/data source hashes still match the Windows verification receipt.</p>', ident="demo"))

chapters = [
    ("1. Introduction", "Configuration problem, motivation, contribution and local-Dask scope.", "F01"),
    ("2. Background and related work", "Tasks, workers, partitions, prediction and uncertainty; primary-paper comparison still needed.", "F01, F11"),
    ("3. Problem formulation", "Candidates, deadline, support, eligibility, balanced score and abstention.", "F02, F10"),
    ("4. Architecture and design", "Offline fitting, inference, evidence and separate research gate.", "F01, F16"),
    ("5. Experimental methodology", "Hardware, datasets, grouped split, timings and research factor design.", "F02-F05, F11"),
    ("6. Implementation and verification", "Module roles, CLI examples and separate software checks.", "F10, F17"),
    ("7. Results and discussion", "Predictions, descriptive cost, screen, Stage A/B and telemetry limits.", "F04, F06-F09, F12-F15, F18"),
    ("8. Conclusion and future work", "Bounded contribution, closed gate and pending fresh evaluation.", "F16, F17"),
]
pages.append(page('<div class="eyebrow">Writing plan</div><h2>Where these assets go in the report</h2><table><tr><th>Chapter</th><th>Content</th><th>Figures</th></tr>' + ''.join(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for a, b, c in chapters) + '</table><p>The earlier blueprint proposes roughly 28-34 total pages including front matter and references, subject to department instructions. This is a writing budget, not a verified university rule. Select the strongest figures for the main text and move detailed diagnostics to appendices.</p><p>Use the seniors’ reports for structural ideas. Do not copy their medical images, model architecture, results, signatures or administrative wording.</p>', ident="chapters"))
pages.append(page("""<div class="eyebrow">Next writing pass</div><h2>What still needs the team’s input</h2>
<table><tr><th>Item</th><th>Current position</th><th>Next action</th></tr>
<tr><td>Front matter</td><td>Team/supervisor names exist in the synopsis handoff.</td><td>Confirm exact title, roll numbers, department, course, designation, session and signature requirements.</td></tr>
<tr><td>Department format</td><td>Senior examples reviewed; official current template not verified.</td><td>Confirm margins, font, cover, certificate and binding instructions before final pagination.</td></tr>
<tr><td>Literature review</td><td>No completed checked bibliography in this pack.</td><td>Read and cite selected primary papers; compare their scope and evaluation fairly.</td></tr>
<tr><td>Fresh advisor validation</td><td>Software passed; no study preparation or collection.</td><td>Review the published receipt before authorizing the separate study.</td></tr>
<tr><td>Research direction</td><td>Probe admission disabled; no useful single-request payback demonstrated.</td><td>Report the negative finding. A new use case needs a revised hypothesis and evaluation plan.</td></tr>
<tr><td>Final delivery</td><td>Exact-dataset advice/execution binding and local interface remain planned.</td><td>Keep planned architecture and measured implementation distinct.</td></tr></table>
<div class="notice warning"><strong>Do not create missing evidence.</strong> No saved training curve or training-accuracy metric is available. Later memory telemetry does not backfill the original table. Scientific results must come from measurements.</div>
<p class="source">Planning reference: SAFE_PIPE_REPORT_BLUEPRINT.html and docs/report_blueprint_evidence.json at research revision edef1cd. The user-supplied senior PDFs remain outside the repository and are not republished.</p>""", ident="gaps"))
nav = '<nav><strong>SAFE-Pipe / Report evidence v1</strong><a href="#overview">Summary</a><a href="#contents">Figures</a><a href="advisor_demo.html">Saved output</a><a href="#gaps">Next steps</a></nav>'
(HERE / "index.html").write_text(document("SAFE-Pipe - Minor B.Tech Project evidence book", nav + '<main>' + ''.join(pages) + '</main>'), encoding="utf-8")

balanced = captures[0][2]
winner = balanced["decision"]["config_id"]
selected = next(c for c in balanced["candidates"] if c["config_id"] == winner)
candidate_rows = ''.join(f'<tr><td><b>{esc(c["config_id"])}</b>{" (selected)" if c["config_id"] == winner else ""}</td><td>{c["predicted_runtime_s"]:.3f} s</td><td>{c["runtime_upper_s"]:.3f} s</td><td>{c["score"]:.4f}</td><td><span class="tag{(" red" if not c["eligible"] else "")}">{"eligible" if c["eligible"] else "rejected"}</span></td></tr>' for c in balanced["candidates"])
demo = page(f'<div class="eyebrow">Saved CLI output / inference only / not the product interface</div><h1 class="demo-title">Why did SAFE-Pipe choose this setting?</h1><p><code>sort_merge</code> fixed profile · balanced mode · 13.1-second engine deadline</p><div class="cards"><div class="card"><b style="font-size:26px">{esc(winner)}</b><span>Selected configuration</span></div><div class="card"><b>{selected["predicted_runtime_s"]:.2f} s</b><span>Point runtime prediction</span></div><div class="card"><b>{selected["runtime_upper_s"]:.2f} s</b><span>Calibrated upper estimate</span></div></div><p>Eligibility checks come first. The lowest declared balanced score among eligible settings wins. The score expresses the selected speed/resource preference; it is not measured cost or money.</p><table><tr><th>Configuration</th><th>Point estimate</th><th>Upper estimate</th><th>Balanced score</th><th>Eligibility</th></tr>{candidate_rows}</table><p class="source">Actual saved output: advisor_capture/sort_balanced.json. Implementation d6f906a; Windows evidence caa8a8a. No Dask workload was run for this capture. Engine time excludes startup and profiling.</p>', ident="saved-advisor")
(HERE / "advisor_demo.html").write_text(document("SAFE-Pipe - saved advisor evidence viewer", '<main>' + demo + '</main>'), encoding="utf-8")
print(f"Assembled {len(pages)} HTML print sections and the saved-output viewer.")
