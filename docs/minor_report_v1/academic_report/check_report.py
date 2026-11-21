"""Verify native Word structure and render the actual report preview for review."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DOCX = ROOT / 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx'
QA = ROOT / 'reports/_scratch/minor_actual_report_v1/word_render'
PDF = QA / 'SAFE_Pipe_DTU_Minor_Project_Report.pdf'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(DOCX) as archive:
    assert archive.testzip() is None
    xml = ET.fromstring(archive.read('word/document.xml'))
    text = ''.join(xml.itertext())
    assert all(s in text for s in ['Daksh Aggarwal','Ganant Awasthi','Chaitanya Singh','23/IT/047','23/IT/055','23/IT/045','Prof. Dinesh Kumar Vishwakarma','2026-2027'])
    assert 'TODO' not in text and 'first draft' not in text
    captions = [p for p in xml.findall('.//w:p',NS) if p.find('w:pPr/w:pStyle[@w:val="Caption"]',NS) is not None]
    content = json.loads((HERE/'report_content.json').read_text(encoding='utf-8'))
    expected = [b for b in content['blocks'] if b['type'] in ('figure','table')]
    assert len(captions) == len(expected) == 23
    assert all(b['title'] in ''.join(p.itertext()) for b,p in zip(expected,captions))
    assert len(xml.findall('.//w:tbl',NS)) == 9
    maths = xml.findall('.//m:oMath',NS)
    assert len(maths) == 4
    denominator = maths[0].find('.//m:f/m:den',NS)
    assert denominator is not None and ''.join(denominator.itertext()).strip() == 'ti'
    assert maths[0].find('.//m:acc',NS) is not None
    media = [n for n in archive.namelist() if n.startswith('word/media/')]
    assert len(media) == 15
    assert not any('vbaProject' in n for n in archive.namelist())
    for chapter in range(1,9):
        assert any(''.join(p.itertext()).startswith(str(chapter)+' ') for p in xml.findall('.//w:p',NS) if p.find('w:pPr/w:pStyle[@w:val="Heading1"]',NS) is not None)

receipt = json.loads((ROOT/'reports/main_validation_windows_checks_v1/verification.json').read_text())
for path, expected_hash in receipt['source_sha256_lf'].items():
    assert hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest() == expected_hash
pdf = pymupdf.open(PDF)
assert len(pdf) == json.loads((HERE/'word_build_result.json').read_text(encoding='utf-8-sig'))['pages']
assert 'Prof. Dinesh Kumar Vishwakarma' in pdf[0].get_text()
assert '23/IT/055' in pdf[0].get_text()
assert pdf[0].get_images(), 'Missing DTU logo on cover'
footers=[]
for i,page in enumerate(pdf):
    assert len(page.get_text().strip()) > 100, f'Nearly blank page {i+1}'
    footers.append(page.get_textbox(pymupdf.Rect(0,page.rect.height-65,page.rect.width,page.rect.height)).strip())
assert footers[0] == ''
assert footers[1:9] == ['i','ii','iii','iv','v','vi','vii','viii']
assert footers[9:] == [str(i) for i in range(1,len(pdf)-8)]
pages=QA/'final_pages';pages.mkdir(exist_ok=True)
for i,page in enumerate(pdf,1):
    page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).save(pages/f'page_{i:02d}.png')
files=[pages/f'page_{i:02d}.png' for i in range(1,len(pdf)+1)]
for group in range((len(files)+3)//4):
    canvas=Image.new('RGB',(1580,2240),'#e0e5eb');draw=ImageDraw.Draw(canvas)
    for j,file in enumerate(files[group*4:(group+1)*4]):
        image=Image.open(file).convert('RGB');image.thumbnail((775,1095))
        x=j%2*790+(790-image.width)//2;y=j//2*1120+22
        canvas.paste(image,(x,y));draw.text((j%2*790+8,j//2*1120+4),file.stem,fill='black')
    canvas.save(QA/f'final_review_{group+1:02d}.png')
summary={'date':'2026-11-22','checks_pass':True,'pages':len(pdf),'chapters':8,'figures':14,
         'tables':9,'native_equations':4,'embedded_images_including_logo':len(media),
         'native_captions_with_titles':len(captions),'front_matter_roman_numbering_checked':True,
         'main_arabic_numbering_restarts_at_one':True,'team_and_guide_details_checked':True,
         'source_receipt_hashes_unchanged':len(receipt['source_sha256_lf']),
         'docx_sha256':hashlib.sha256(DOCX.read_bytes()).hexdigest(),
         'preview_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
         'rendering':'Native Microsoft Word 16 PDF save, rasterized with PyMuPDF for page review.',
         'scope':'Academic report production only. No new benchmark, dataset generation, training or main merge.'}
(HERE/'report_quality.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
