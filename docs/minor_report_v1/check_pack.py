"""Check report provenance, numerical denominators, links and rendered outputs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
import csv
import hashlib
import json
import subprocess
import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
register = json.loads((HERE / "figure_register.json").read_text())
manifest = json.loads((HERE / "source_manifest.json").read_text())
facts = json.loads((HERE / "verified_facts.json").read_text())
assert len(register) == 18
assert len(list((HERE / "figures").glob("*.png"))) == len(register)
assert len(list((HERE / "figures").glob("*.svg"))) == len(register)
assert len(list((HERE / "tables").glob("*.csv"))) == 13
for source in manifest["inputs"]:
    data = subprocess.check_output(["git", "show", f"{source['revision']}:{source['path']}"], cwd=ROOT)
    assert hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest() == source["sha256_lf"], source["path"]
receipt = json.loads((ROOT / "reports/main_validation_windows_checks_v1/verification.json").read_text())
for path, expected in receipt["source_sha256_lf"].items():
    assert hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == expected, path
assert round(facts["test_mdape_percent"], 2) == 13.84
assert round(facts["baseline_mdape_percent"], 2) == 23.01
assert facts["stage_a_statuses"] == {"execution_error": 7, "success": 41}
assert facts["stage_b_pressure_discrepancy_groups"] == 8
assert facts["probe_admission_enabled"] is False and facts["fresh_main_study_cells"] == 0
with (HERE / "tables/terminated_worker_memory.csv").open(newline="") as f:
    workers = list(csv.DictReader(f))
assert len(workers) == 37
assert sum(float(w["saved_peak_over_cap"]) < float(w["termination_threshold_ratio"]) for w in workers) == 33
assert sum(float(w["event_rss_bytes"]) > float(w["saved_peak_rss_bytes"]) for w in workers) == 36
commands = json.loads((HERE / "advisor_capture/commands.json").read_text())
assert len(commands) == 4
for command in commands:
    assert command["argv"][1:4] == ["-m", "safe_pipe.cli", "advise"]
    data = (HERE / "advisor_capture" / command["stdout"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == command["sha256"]
assert json.loads((HERE / "advisor_capture/sort_abstain.json").read_text())["decision"]["action"] == "abstain"


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = set(); self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("src", "href"):
            if attrs.get(key): self.links.append(attrs[key])


links_checked = 0
for name in ["index.html", "advisor_demo.html"]:
    parser = Links(); parser.feed((HERE / name).read_text(encoding="utf-8"))
    for link in parser.links:
        if link.startswith("#"):
            assert link[1:] in parser.ids, link
        elif "://" not in link:
            assert (HERE / unquote(link.split("#")[0])).exists(), link
        links_checked += 1
for figure in register:
    with Image.open(HERE / "figures" / f"{figure['id']}.png") as img:
        assert img.width >= 1500 and img.height >= 500
pdf_path = ROOT / "output/pdf/safe_pipe_minor_report_v1/SAFE_Pipe_Minor_Report_Evidence_v1.pdf"
doc = pymupdf.open(pdf_path)
assert len(doc) == 24, f"Expected one page per print section; got {len(doc)}"
for i, page in enumerate(doc, 1):
    text = page.get_text()
    assert len(text.strip()) > 100, f"Blank or nearly blank page {i}"
    assert f"{i} / {len(doc)}" in text, f"Missing page number {i}"
for i in range(3, 3 + len(register)):
    assert doc[i].get_images(), f"Figure missing on page {i+1}"
qa = ROOT / "reports/_scratch/minor_report_v1/final_pdf_pages"
qa.mkdir(parents=True, exist_ok=True)
for i, page in enumerate(doc, 1):
    page.get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2), alpha=False).save(qa / f"page_{i:02d}.png")
report = {"date": "2026-11-21", "checks_pass": True, "figures": len(register), "figure_formats": ["PNG 240 dpi", "SVG with text"],
          "csv_tables": 13, "pdf_pages": len(doc), "pdf_bytes": pdf_path.stat().st_size,
          "source_manifest_entries_checked": len(manifest["inputs"]), "original_receipt_hashes_unchanged": len(receipt["source_sha256_lf"]),
          "html_links_checked": links_checked, "inference_only_captures": len(commands),
          "all_pdf_pages_rendered_for_visual_review": True,
          "scope": "Report analysis/rendering and inference only; no new benchmarks, original data generation, training, study preparation or main merge.",
          "software_suite_rerun": False, "existing_main_suite_result": receipt["tests"],
          "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest()}
(HERE / "quality_report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
