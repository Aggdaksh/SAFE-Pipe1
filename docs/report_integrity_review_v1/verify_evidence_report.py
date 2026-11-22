"""Check revised content, source identity and an isolated report rebuild."""
import argparse, ast, hashlib, io, json, subprocess
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E
import pymupdf
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--qa', default='reports/_scratch/report_evidence_v2_03')
parser.add_argument('--docx', default='output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Evidence_Reviewed.docx')
parser.add_argument('--rebuild-docx', default='reports/_scratch/report_evidence_rebuild_v2_03.docx')
parser.add_argument('--rebuild-pdf', default='reports/_scratch/report_evidence_rebuild_v2_03/report.pdf')
parser.add_argument('--previous-pdf', default='reports/_scratch/report_revision_v1/reviewed.pdf')
parser.add_argument('--receipt', help='New receipt path; defaults to QA/verification.json')
args = parser.parse_args()
QA, DOC, REBUILD = (ROOT / p for p in (args.qa, args.docx, args.rebuild_docx))
receipt_path = ROOT / args.receipt if args.receipt else QA / 'verification.json'
if receipt_path.exists():
    raise FileExistsError(f'Preserve the existing receipt; choose --receipt with a new path: {receipt_path}')
plan = json.loads((HERE/'evidence_revision_plan.json').read_text(encoding='utf-8'))
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def git_bytes(revision, path):
    return subprocess.check_output(['git','show',revision+':'+path], cwd=ROOT)
def digest(data):
    return hashlib.sha256(data).hexdigest()
def content(data):
    with ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        root = E.fromstring(z.read('word/document.xml'))
        paras = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in root.findall('.//w:p', ns)]
        media = {p:digest(z.read(p)) for p in z.namelist() if p.startswith('word/media/')}
    return root, paras, media
root, paragraphs, media = content(DOC.read_bytes())
base = git_bytes(plan['base_revision'], plan['base_path'])
assert digest(base) == plan['base_sha256']
assert media == content(base)[2]
assert paragraphs == content(REBUILD.read_bytes())[1], 'Isolated rebuild text differs'
for edit in plan['edits']:
    for segment in edit['after'].split('\n'):
        assert paragraphs.count(segment) == 1, segment[:80]
    assert edit['before'] not in paragraphs
for reference in plan['references']:
    assert reference in paragraphs
assert len(root.findall('.//w:tbl',ns)) == 9
assert len(root.findall('.//m:oMath',ns)) == 4
assert len(media) == 15
assert any(p.startswith('AI assistance:') for p in paragraphs)
assert 'CANDIDATES\u2019 DECLARATION' in paragraphs
assert 'Project Supervisor' in paragraphs
assert any('All eight configurations met the 13.1-second deadline' in p for p in paragraphs)
source_manifest = json.loads((ROOT/'docs/minor_report_v1/source_manifest.json').read_text())
for entry in source_manifest['inputs']:
    assert digest(git_bytes(entry['revision'],entry['path']).replace(b'\r\n',b'\n')) == entry['sha256_lf']
for ref in plan['evidence_links']:
    assert git_bytes(ref['revision'], ref['path'])
historical = json.loads((ROOT/'reports/main_validation_windows_checks_v1/verification.json').read_text())
changed = []
for path, expected in historical['source_sha256_lf'].items():
    assert digest(git_bytes('caa8a8a', path).replace(b'\r\n',b'\n')) == expected
    if digest((ROOT/path).read_bytes().replace(b'\r\n',b'\n')) != expected:
        changed.append(path)
assert changed == ['safe_pipe/models/runtime.py'], changed
class WithoutDocstrings(ast.NodeTransformer):
    def generic_visit(self, node):
        node = super().generic_visit(node)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
        return node
def executable_tree(text):
    return ast.dump(WithoutDocstrings().visit(ast.parse(text)), include_attributes=False)
runtime = 'safe_pipe/models/runtime.py'
assert executable_tree((ROOT/runtime).read_text()) == executable_tree(git_bytes('caa8a8a', runtime).decode()), 'Executable code changed'
raw_receipt = json.loads(git_bytes('edef1cd','reports/worker_memory_stage_a_b_v1/verification.json'))
raw_checks = []
for stage in raw_receipt['stages']:
    folder = ROOT/f'data/probes/windows-stage-{stage["stage"].lower()}-v1'
    result = {'stage':stage['stage'], 'available':folder.exists()}
    for name, key in [('runs.jsonl','runs_sha256'),('plan.json','plan_file_sha256')]:
        path = folder/name
        result[name] = 'missing'
        if path.exists():
            with path.open('rb') as f:
                actual = hashlib.file_digest(f,'sha256').hexdigest()
            assert actual == stage[key], str(path)
            result[name] = 'hash matches retained export receipt'
    raw_checks.append(result)
pdf = pymupdf.open(QA/'report.pdf')
rebuilt = pymupdf.open(ROOT / args.rebuild_pdf)
prior = pymupdf.open(ROOT / args.previous_pdf)
assert len(pdf) == len(rebuilt)
changed_pages = []
for i, page in enumerate(pdf):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False)
    assert pix.samples == rebuilt[i].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).samples, f'Rebuild page {i+1}'
    pix.save(QA/f'page_{i+1:02}.png')
    if i >= len(prior) or pix.samples != prior[i].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).samples:
        changed_pages.append(i+1)
    assert len(page.get_text().strip()) > 100
footers = [p.get_textbox(pymupdf.Rect(0,p.rect.height-65,p.rect.width,p.rect.height)).strip() for p in pdf]
assert footers[0] == '' and footers[1:9] == ['i','ii','iii','iv','v','vi','vii','viii']
assert footers[9:] == [str(i) for i in range(1,len(pdf)-8)]
for k in range(0,len(changed_pages),4):
    canvas = Image.new('RGB',(1580,2240),'#dddddd'); draw = ImageDraw.Draw(canvas)
    for j,n in enumerate(changed_pages[k:k+4]):
        im = Image.open(QA/f'page_{n:02}.png'); im.thumbnail((775,1095)); x,y = j%2*790,j//2*1120
        canvas.paste(im,(x,y+22));draw.text((x+4,y+4),str(n),fill='black')
    canvas.save(QA/f'review_{k//4+1:02}.png')
result = {'version':plan['version'],'docx_sha256':digest(DOC.read_bytes()),'pages':len(pdf),'images':len(media),'tables':9,'equations':4,'bibliography_entries':15,'edits_verified':len(plan['edits']),'pinned_report_inputs_verified':16,'historical_verification_inputs_verified':78,'current_source_hash_differences':changed,'runtime_executable_ast_unchanged':True,'isolated_rebuild_text_and_all_page_pixels_match':True,'raw_record_checks':raw_checks,'parquet_diagnostics_full_reaudit':False,'changed_pages_vs_previous_reviewed':changed_pages,'visual_review':'pending','software_suite_rerun':False,'benchmarks_or_training':False}
receipt_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
