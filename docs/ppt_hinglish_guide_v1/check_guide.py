"""Read-only artifact QA plus page renders; never runs SAFE-Pipe experiments."""
import hashlib
import json
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
receipt=json.loads((HERE/'build_receipt.json').read_text(encoding='utf-8'))
out=ROOT/'output/pdf/SAFE_Pipe_PPT_Hinglish_Step_by_Step_Guide.pdf'
qa=ROOT/'reports/_scratch/ppt_hinglish_guide_v1/qa'
qa.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(out.read_bytes()).hexdigest()==receipt['output_pdf_sha256']
source=Path(receipt['source_pdf'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==receipt['source_pdf_sha256']
doc=pymupdf.open(out);slides=pymupdf.open(source)
assert len(doc)==receipt['pages']==55
assert len(doc[1].get_links())==11
source_ids={s['id'] for s in receipt['sources']}
all_notes=[]
for i,(page,item) in enumerate(zip(doc,receipt['page_map'])):
    assert i+1==item['page']
    text=page.get_text()
    assert len(text.strip())>80, f'Unexpected blank page {i+1}'
    if item['kind']=='slide':
        original=slides[item['slide']-1]
        assert page.rect==original.rect
        assert page.get_pixmap(matrix=pymupdf.Matrix(1,1)).samples==original.get_pixmap(matrix=pymupdf.Matrix(1,1)).samples
        assert text==original.get_text()
    else:
        all_notes.append(text)
        assert '\ufffd' not in text, f'Missing glyph on {i+1}'
        for b in page.get_text('dict')['blocks']:
            if 'lines' not in b:continue
            for line in b['lines']:
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    assert x0>=-0.5 and y0>=-0.5 and x1<=page.rect.width+0.5 and y1<=page.rect.height+0.5, (i+1,span['text'])
    page.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3),alpha=False).save(qa/f'page_{i+1:02}.png')
for start in range(0,len(doc),6):
    c=Image.new('RGB',(1500,1450),'#d9e0e2');draw=ImageDraw.Draw(c)
    for j in range(start,min(start+6,len(doc))):
        im=Image.open(qa/f'page_{j+1:02}.png');im.thumbnail((490,690))
        x=(j-start)%3*500;y=(j-start)//3*725
        c.paste(im,(x+(490-im.width)//2,y+25));draw.text((x+8,y+5),f'Page {j+1}',fill='black')
    c.save(qa/f'contact_{start//6+1:02}.png')
joined='\n'.join(all_notes)
for term in ['uniform_memory','partition_tail','13.84','23.01','652,653,184','10.37','4.79','143','38','6.78','10.96','exchangeability','34.1']:
    assert term in joined,term
quality=dict(pages=len(doc),original_slides_pixel_and_text_identical=11,internal_contents_links=11,bookmarks=len(doc.get_toc()),typed_text_searchable=True,no_missing_glyph_markers=True,no_text_outside_pages=True,source_pdf_unchanged=True,rendered_pages=len(doc),visual_review='pending',no_benchmarks_or_training=True)
(HERE/'quality_receipt.json').write_text(json.dumps(quality,indent=2)+'\n',encoding='utf-8')
print(json.dumps(quality,indent=2))
