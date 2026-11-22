"""Build the Hinglish slide companion from pinned evidence and original PDF pages.

Only reads existing project evidence. No imports of experiment runners or models.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENDOR = ROOT / 'reports/_scratch/ppt_hinglish_guide_v1/pdf_deps'
if VENDOR.exists():
    sys.path.insert(0, str(VENDOR))
import pymupdf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from content import PAGES

MAIN = 'caa8a8a919d7cf4822e1735c795d22c31b63dc71'
RESEARCH = 'edef1cdbba0d980bc1a359960d7339cc08d13d84'
CURRENT = '8179c0737624560351fa4d5ca5a23a8f767329ff'
SOURCES = {
 'M1': ('Current scope aur pending work', CURRENT, ['context.md']),
 'M2': ('Dataset/feature/timing dictionary', MAIN, ['docs/DATA_DICTIONARY.md']),
 'M3': ('Model inputs aur fitting code', CURRENT, ['safe_pipe/features.py','experiments/train_runtime.py','safe_pipe/models/runtime.py']),
 'M4': ('Advisor checks aur balanced formula', MAIN, ['docs/CONFIG_SELECTION.md']),
 'M5': ('Frozen datasets aur actual operators', MAIN, ['configs/datasets_main_v1.json','configs/dask_grid.json','safe_pipe/workloads/execute_dask.py']),
 'M6': ('Original measured run table', MAIN, ['data/curated/runs.csv']),
 'M7': ('Windows validation handoff', CURRENT, ['docs/WINDOWS_MAIN_VALIDATION.md']),
 'M8': ('Grouped model methodology', MAIN, ['reports/runtime_model.md','configs/model_split_main_v1.json']),
 'M9': ('Saved test metrics aur predictions', MAIN, ['artifacts/main_v1/runtime_metrics.json','artifacts/main_v1/runtime_test_predictions.csv']),
 'M10': ('Historical storage explanation', CURRENT, ['docs/minor_report_v1/REPORT_DRAFT.md']),
 'M11': ('Saved balanced recommendation', CURRENT, ['docs/minor_report_v1/advisor_capture/sort_balanced.json']),
 'M12': ('Windows test receipt aur audit follow-up', CURRENT, ['reports/main_validation_windows_checks_v1/verification.json','docs/report_integrity_review_v1/evidence_revision_receipt.json']),
 'M13': ('Older 34.1 percent historical replay', MAIN, ['reports/policy.md','reports/policy_metrics.json']),
 'R1': ('Initial four-method screen protocol', RESEARCH, ['docs/research/PROBE_PROTOCOL.md']),
 'R2': ('Completed screen aur ranking review', RESEARCH, ['reports/research_probe_windows_mains_v1_complete/summary.json','reports/research_screen_review_20261114/RESULTS.md']),
 'R3': ('Stage A recipe aur full outcomes', RESEARCH, ['configs/research_stage_a_v1.json','reports/research_stage_a_windows_v1/REPORT.md']),
 'R4': ('Stage B recipe aur interpretation', RESEARCH, ['configs/research_stage_b_v1.json','docs/research/STAGE_B_REVIEW.md']),
 'R5': ('Stage B compact measurements', RESEARCH, ['reports/research_stage_b_windows_v1/summary.json','reports/research_stage_b_windows_v1/findings.json']),
 'R6': ('Worker memory export aur review', RESEARCH, ['reports/worker_memory_review_20261116/README.md','reports/worker_memory_stage_a_b_v1/verification.json']),
 'R7': ('One-probe cost aur feasibility', RESEARCH, ['reports/one_probe_feasibility_20261116/README.md','reports/one_probe_feasibility_20261116/analysis.json']),
 'R8': ('Research Windows verification', RESEARCH, ['reports/one_probe_windows_checks_v1/verification.json','reports/one_probe_windows_checks_v1/WINDOWS_TEST_OUTPUT.txt']),
 'R9': ('Disabled prototype contract', RESEARCH, ['docs/research/ONE_PROBE_SPEC.md','configs/research_one_probe_v1.json']),
 'E1': ('Dask worker memory: official reference', None, ['https://distributed.dask.org/en/stable/worker-memory.html']),
 'E2': ('LightGBM: official feature overview', None, ['https://lightgbm.readthedocs.io/en/stable/Features.html']),
}

def git_read(revision, path):
    return subprocess.check_output(['git','show',f'{revision}:{path}'],cwd=ROOT)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def source_manifest():
    result = []
    for key, (title, revision, paths) in SOURCES.items():
        item = dict(id=key,title=title,revision=revision,files=[])
        for path in paths:
            if revision:
                data = git_read(revision,path)
                item['files'].append(dict(path=path,sha256_lf=sha(data.replace(b'\r\n',b'\n'))))
            else:
                item['files'].append(dict(url=path,accessed='2026-11-23'))
        result.append(item)
    return result

NAVY='#193443';TEAL='#087F83';GRAY='#556772';PALE='#ECF5F4'
W,H=595.276,841.89
for name,path in [('Guide','C:/Windows/Fonts/arial.ttf'),('GuideBold','C:/Windows/Fonts/arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name,path))
pdfmetrics.registerFontFamily('Guide',normal='Guide',bold='GuideBold',italic='Guide',boldItalic='GuideBold')
STYLE={
 'body':ParagraphStyle('body',fontName='Guide',fontSize=11.2,leading=15.7,textColor=HexColor(NAVY),spaceAfter=8),
 'heading':ParagraphStyle('heading',fontName='GuideBold',fontSize=11.6,leading=15,textColor=HexColor(TEAL)),
 'title':ParagraphStyle('title',fontName='GuideBold',fontSize=23,leading=28,textColor=HexColor(NAVY)),
 'small':ParagraphStyle('small',fontName='Guide',fontSize=8.6,leading=12,textColor=HexColor(GRAY)),
 'source':ParagraphStyle('source',fontName='Guide',fontSize=9.4,leading=13,textColor=HexColor(NAVY),splitLongWords=1),
}

def draw_para(c,text,x,y,width,style='body'):
    p=Paragraph(text,STYLE[style]);_,height=p.wrap(width,1000)
    p.drawOn(c,x,y-height)
    return y-height

def text_pdf(item,number,total):
    bio=io.BytesIO();c=canvas.Canvas(bio,pagesize=(W,H))
    c.setFillColor(HexColor(TEAL));c.rect(0,H-8,W,8,fill=1,stroke=0)
    label=f"SLIDE {item['slide']:02} / HINGLISH EXPLANATION" if 1<=item['slide']<=11 else item.get('label','REVISION / EVIDENCE')
    c.setFont('GuideBold',8);c.setFillColor(HexColor(GRAY));c.drawString(43,H-35,label)
    y=draw_para(c,escape(item['title']),43,H-56,W-86,'title')-20
    for heading,body in item['blocks']:
        if heading:
            y=draw_para(c,escape(heading),43,y,W-86,'heading')-5
        y=draw_para(c,body,43,y,W-86,'source' if item.get('sources') else 'body')-12
    if y<67:
        raise ValueError(f'Content overflows page {number}: {item["title"]}; bottom={y}')
    c.setStrokeColor(HexColor('#CCDADD'));c.line(43,53,W-43,53)
    if item.get('refs'):
        refs='Evidence: '+', '.join(item['refs'])+' | full file map guide ke end mein'
    else:
        refs='SAFE-Pipe | Personal study companion | 23 November 2026'
    draw_para(c,escape(refs),43,44,W-138,'small')
    c.setFont('Guide',8.5);c.setFillColor(HexColor(GRAY));c.drawRightString(W-43,29,f'{number} / {total}')
    c.save();return bio.getvalue()

def cover_pdf(total):
    bio=io.BytesIO();c=canvas.Canvas(bio,pagesize=(W,H))
    c.setFillColor(HexColor(NAVY));c.rect(0,H-295,W,295,fill=1,stroke=0)
    c.setFillColor(HexColor('#A4D6CD'));c.setFont('GuideBold',12);c.drawString(46,H-60,'SLIDE-BY-SLIDE STUDY COMPANION')
    c.setFillColor(HexColor('#FFFFFF'));c.setFont('GuideBold',44);c.drawString(43,H-127,'SAFE-Pipe')
    c.setFont('GuideBold',24);c.drawString(46,H-174,'Project ko samjho,')
    c.drawString(46,H-208,'sirf slides mat yaad karo.')
    c.setFont('Guide',11);c.drawString(46,H-254,'Roman Hinglish | 11 original slides + detailed lessons')
    y=H-340
    for title,body in [
      ('Is guide mein kya milega?', 'Aapki original PPT ke har page ke baad easy explanation, worked examples, graph-reading notes aur evidence locations. Basics se start karke model, probes, memory aur current status tak poori story.'),
      ('Kaise padhna hai?', 'Pehle original slide dekho. Phir uske explanation pages padho. Last mein speaking script se apne words mein practice karo. Bold terms aur number map quick revision ke liye hain.'),
      ('Evidence ki boundary', 'Original slide pages unchanged hain. Explanations project records se checked hain. Teaching examples measured results se alag labelled hain. No new experiments or training were run for this guide.'),
    ]:
        y=draw_para(c,title,46,y,W-92,'heading')-7
        y=draw_para(c,body,46,y,W-92)-22
    c.setFont('Guide',9);c.setFillColor(HexColor(GRAY));c.drawString(46,58,'Prepared 23 November 2026 | DTU Minor B.Tech Project | Group 45')
    c.drawString(46,41,f'{total} pages | Source deck dated 22 November 2026')
    c.save();return bio.getvalue()

def append_sources(items):
    entries=list(SOURCES.items())
    for k in range(0,len(entries),4):
        blocks=[]
        for key,(title,revision,paths) in entries[k:k+4]:
            lines=[]
            for path in paths:
                url=f'https://github.com/Aggdaksh/SAFE-Pipe1/blob/{revision}/{path}' if revision else path
                lines.append(f'<link href="{escape(url)}" color="{TEAL}">{escape(path)}</link>')
            tail=f'Revision: {revision[:7]}. ' if revision else 'Official docs accessed 23 November 2026. '
            tail+='Link click karke file padho; local checkout mein research file absent ho toh pinned Git version dekho.' if revision else 'Definitions ke liye; project result ka proof local experiment records hain.'
            blocks.append((f'[{key}] {title}','<br/>'.join(lines)+'<br/>'+tail))
        items.append(dict(kind='text',slide=0,title=f'Evidence file map {k//4+1}',blocks=blocks,refs=[],sources=True,label='FILE MAP / CLICKABLE SOURCES'))

def build(source_path,output_path):
    original=pymupdf.open(source_path)
    if len(original)!=11:
        raise ValueError('Expected the reviewed eleven-slide deck')
    manifest=source_manifest()
    # These are read-only checks of saved metrics, not model inference or tests.
    metrics=json.loads(git_read(MAIN,'artifacts/main_v1/runtime_metrics.json'))
    assert round(metrics['test_mdape_percent'],2)==13.84
    assert round(metrics['median_baseline_test_mdape_percent'],2)==23.01
    assert (metrics['train_rows'],metrics['calibration_rows'],metrics['test_rows'])==(36,36,24)
    check=json.loads(git_read(RESEARCH,'reports/one_probe_windows_checks_v1/verification.json'))
    assert (check['tests_passed'],check['default_decisions_checked'],check['single_observation_decisions_checked'],check['termination_records_checked'])==(38,8,24,37)
    assert not check['admission_enabled'] and check['physical_attempts_executed']==0
    items=[dict(kind='cover',title='SAFE-Pipe Hinglish guide'),dict(kind='contents',title='Guide ka reading map')]
    for n in range(1,12):
        items.append(dict(kind='slide',slide=n,title=f'Original PPT slide {n}'))
        items.extend(dict(kind='text',**p) for p in PAGES if p['slide']==n)
    items.extend(dict(kind='text',**p) for p in PAGES if p['slide']==12)
    items.append(dict(kind='text',slide=0,title='Evidence khud kaise check karna hai?',label='READ-ONLY REPOSITORY WALKTHROUGH',refs=['M1','M3','M9','R3','R4','R8'],blocks=[
      ('1. File names ko samjho', 'CSV table hoti hai: each row ek record. JSON structured object/list hota hai. JSONL mein each line separate record hota hai, isliye large run log append ho sakta hai. MD plain-text documentation hai. Python script analysis/implementation ho sakti hai; sirf file open karne se experiment run nahi hota.'),
      ('2. Original model result verify karo', 'VS Code Explorer mein artifacts/main_v1/runtime_metrics.json kholo: test_mdape_percent aur test_rows dekho. runtime_test_predictions.csv mein actual engine_seconds aur predicted_seconds compare karo. Split configs/model_split_main_v1.json mein hai; input whitelist safe_pipe/features.py mein.'),
      ('3. Research results inspect karo', 'Research files current branch mein absent ho sakti hain. Next pages ke pinned GitHub links use karo, ya terminal mein read-only git show edef1cd:docs/research/STAGE_B_REVIEW.md chalao. Branch switch/pull ya experiment commands is reading ke liye required nahi.'),
      ('4. Result ke source tak jao', 'README/REPORT se meaning samjho; measurements/summary se counts check karo; verification receipt se version/hash check karo. Retained raw JSONL aur diagnostics Windows host par ignored directories mein hain. Compact export raw backup ka substitute nahi; source records kisi field ko unknown bolein toh zero assume mat karo.'),
      ('5. Slide notes ka scope', 'Original slides preserve ki hain, partner ki PPT edit nahi ki. Slide 2 ka reserve wording configured cap hai. Slide 4 join rows declared-left rows hain. Slide 5 error test metric hai. Slide 9 timings reconstructed hain. Slide 10 historical test receipts ko current new experiment mat samjho.'),
    ]))
    append_sources(items)
    total=len(items)
    rows=[]
    for n in range(1,12):
        index=next(i for i,x in enumerate(items) if x['kind']=='slide' and x['slide']==n)
        last=index+sum(p['slide']==n for p in PAGES)
        titles=['Purpose aur basics','Timeline, branches, storage','Architecture aur profiling','Workloads, configs, datasets','LightGBM, split, error, upper estimate','Balanced scoring worked example','Screen, four methods, Stage A','Stage B aur memory evidence','One-probe cost aur disabled gate','Tests versus fresh validation','Limits aur next milestones']
        rows.append((f'Slide {n:02} | guide pages {index+1}-{last+1}',titles[n-1]))
    # A compact navigation page with links to each original slide.
    bio=io.BytesIO();c=canvas.Canvas(bio,pagesize=(W,H));c.setFillColor(HexColor(TEAL));c.rect(0,H-8,W,8,fill=1,stroke=0)
    y=draw_para(c,'Guide ka reading map',43,H-48,W-86,'title')-18
    y=draw_para(c,'Original slides landscape mein hain; explanations portrait pages par typed, searchable Roman Hinglish mein hain. PDF bookmarks se bhi jump kar sakte ho.',43,y,W-86)-16
    for heading,body in rows:
        y=draw_para(c,heading,43,y,W-86,'heading')-3;y=draw_para(c,body,43,y,W-86)-11
    y=draw_para(c,'Last section: number revision map, viva answers, speaking script aur clickable evidence file map. Har explanation ke footer mein source IDs hain.',43,y,W-86,'small')
    if y<45:raise ValueError('Contents overflow')
    c.setFont('Guide',8.5);c.drawRightString(W-43,28,f'2 / {total}');c.save();toc_pdf=bio.getvalue()
    result=pymupdf.open();toc=[];mapping=[]
    for number,item in enumerate(items,1):
        if item['kind']=='slide':
            result.insert_pdf(original,from_page=item['slide']-1,to_page=item['slide']-1)
            toc.append([1,f'Slide {item["slide"]}: '+rows[item['slide']-1][1],number])
        else:
            raw=cover_pdf(total) if item['kind']=='cover' else toc_pdf if item['kind']=='contents' else text_pdf(item,number,total)
            with pymupdf.open(stream=raw,filetype='pdf') as part:result.insert_pdf(part)
            toc.append([2 if item.get('slide',0) in range(1,12) else 1,item['title'],number])
        mapping.append(dict(page=number,title=item['title'],kind=item['kind'],slide=item.get('slide')))
    result.set_toc(toc)
    # Add contents-page internal links without altering original slide pages.
    contents=result[1]
    for n,(heading,_) in enumerate(rows,1):
        dest=next(m['page']-1 for m in mapping if m['kind']=='slide' and m['slide']==n)
        for rect in contents.search_for(heading):contents.insert_link({'kind':pymupdf.LINK_GOTO,'from':rect,'page':dest})
    result.set_metadata(dict(title='SAFE-Pipe - Roman Hinglish slide-by-slide guide',author='SAFE-Pipe project study companion',subject='Original presentation with verified beginner explanations',keywords='Hinglish SAFE-Pipe Dask LightGBM probes viva'))
    output_path.parent.mkdir(parents=True,exist_ok=True)
    result.save(output_path,garbage=4,deflate=True)
    result.close()
    receipt=dict(date='2026-11-23',source_pdf=str(source_path),source_pdf_sha256=sha(source_path.read_bytes()),output_pdf_sha256=sha(output_path.read_bytes()),pages=total,original_slides=11,explanation_pages=len(PAGES),typed_note_word_count=sum(len(re.sub('<[^>]+>',' ',p['title']+' '+' '.join(h+' '+b for h,b in p['blocks'])).split()) for p in PAGES),page_map=mapping,sources=manifest,no_experiments_or_training=True,visual_review='pending')
    (HERE/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['sources','page_map']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('C:/Users/Ganant Awasthi/Downloads/BTP_new_PPT.pdf'))
    parser.add_argument('--out',type=Path,default=ROOT/'output/pdf/SAFE_Pipe_PPT_Hinglish_Step_by_Step_Guide.pdf')
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(f'Choose a new output path: {args.out}')
    build(args.source,args.out)
