from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E
import hashlib, json
import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
QA = ROOT/'reports/_scratch/report_revision_v1'
plan = json.loads((BASE/'revision_plan.json').read_text(encoding='utf-8'))
original = ROOT/'output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx'
revised = original.with_name('SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx')
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
with ZipFile(revised) as z:
    assert z.testzip() is None
    root = E.fromstring(z.read('word/document.xml'))
    paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in root.findall('.//w:p', ns)]
    for edit in plan['edits']:
        assert paragraphs.count(edit['after']) == 1, edit['id']
    assert plan['disclosure'] in paragraphs
    assert len(root.findall('.//w:tbl', ns)) == 9
    assert len(root.findall('.//m:oMath', ns)) == 4
    media = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
with ZipFile(original) as z:
    assert media == {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
assert sha(original) == '8df622f1c106665459e34cd72d060a1f1350f228e3a45f1d011e2a0370f62a1b'
receipt = json.loads((ROOT/'reports/main_validation_windows_checks_v1/verification.json').read_text())
for path, expected in receipt['source_sha256_lf'].items():
    assert hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected
pdf = pymupdf.open(QA/'reviewed.pdf')
old = pymupdf.open(ROOT/'reports/_scratch/minor_actual_report_v1/word_render/SAFE_Pipe_DTU_Minor_Project_Report.pdf')
changed = []
for i, page in enumerate(pdf):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3), alpha=False)
    pix.save(QA/f'page_{i+1:02}.png')
    if i >= len(old) or pix.samples != old[i].get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3), alpha=False).samples:
        changed.append(i+1)
    assert len(page.get_text().strip()) > 100
footers = [p.get_textbox(pymupdf.Rect(0, p.rect.height-65, p.rect.width, p.rect.height)).strip() for p in pdf]
assert footers[0] == '' and footers[1:9] == ['i','ii','iii','iv','v','vi','vii','viii']
assert footers[9:] == [str(i) for i in range(1, len(pdf)-8)]
for k in range(0, len(changed), 4):
    canvas = Image.new('RGB', (1580, 2240), '#dddddd')
    draw = ImageDraw.Draw(canvas)
    for j, n in enumerate(changed[k:k+4]):
        im = Image.open(QA/f'page_{n:02}.png'); im.thumbnail((775, 1095))
        x, y = j%2*790, j//2*1120
        canvas.paste(im, (x,y+22)); draw.text((x+4,y+4), str(n), fill='black')
    canvas.save(QA/f'review_{k//4+1:02}.png')
summary = {'date':'2026-11-22', 'source_sha256':sha(original), 'reviewed_sha256':sha(revised),
           'pages':len(pdf), 'applied_edits':[e['id'] for e in plan['edits']],
           'disclosure_added':True, 'images_preserved':len(media), 'tables':9, 'equations':4,
           'source_preserved':True, 'original_evidence_hashes_preserved':len(receipt['source_sha256_lf']),
           'pages_changed_from_original_render':changed, 'visual_review':'pending',
           'rendering':'Native Word PDF save; existing PyMuPDF rasterizer. Managed document runtime unavailable.',
           'production_note':'Corrected disclosure paragraph break; receipt computed after Word closed the output file.'}
(BASE/'revision_receipt.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
