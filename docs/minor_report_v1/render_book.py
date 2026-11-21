"""Print the offline evidence book and capture its HTML in isolated headless Chrome.

No existing browser profile is used. No package is installed or project job run.
"""
from pathlib import Path
import subprocess
import sys
import pymupdf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "output/pdf/safe_pipe_minor_report_v1"
SCRATCH = ROOT / "reports/_scratch/minor_report_v1"
OUT.mkdir(parents=True, exist_ok=True)
shots = HERE / "screenshots"
shots.mkdir(exist_ok=True)
browser = next((p for p in [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")] if p.exists()), None)
if browser is None:
    raise RuntimeError("No installed Chrome/Edge found; print index.html to PDF manually.")
base = [str(browser), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        "--disable-background-networking", "--disable-extensions", "--allow-file-access-from-files",
        "--hide-scrollbars", "--virtual-time-budget=4000", f"--user-data-dir={SCRATCH / 'browser_profile'}"]
jobs = [
    ([f"--print-to-pdf={SCRATCH / 'raw_book.pdf'}", "--no-pdf-header-footer"], HERE / "index.html"),
    ([f"--screenshot={shots / 'report_cover.png'}", "--window-size=1440,1100"], HERE / "index.html"),
    ([f"--screenshot={shots / 'saved_advisor_output.png'}", "--window-size=1440,1250"], HERE / "advisor_demo.html"),
]
for extra, page in jobs:
    result = subprocess.run(base + extra + [page.as_uri()], capture_output=True, timeout=90,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    logname = "print" if "print-to-pdf" in extra[0] else page.stem
    (SCRATCH / f"browser_{logname}.txt").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Browser rendering failed for {page.name}; see scratch log.")
doc = pymupdf.open(SCRATCH / "raw_book.pdf")
for number, pdf_page in enumerate(doc, 1):
    footer = f"SAFE-Pipe | Evidence v1 | {number} / {len(doc)}"
    pdf_page.insert_textbox(pymupdf.Rect(38, pdf_page.rect.height - 27, pdf_page.rect.width - 38, pdf_page.rect.height - 12), footer, fontsize=8, fontname="helv", color=(.32, .39, .46), align=1)
doc.set_metadata({"title": "SAFE-Pipe - Minor B.Tech Project Report Evidence v1", "subject": "Working evidence pack; not a final academic submission"})
doc.save(OUT / "SAFE_Pipe_Minor_Report_Evidence_v1.pdf", garbage=4, deflate=True)
doc.close()
for file in [OUT / "SAFE_Pipe_Minor_Report_Evidence_v1.pdf", shots / "report_cover.png", shots / "saved_advisor_output.png"]:
    if not file.exists() or file.stat().st_size == 0:
        raise RuntimeError(f"Missing browser output: {file}")
    print(file.relative_to(ROOT).as_posix())
