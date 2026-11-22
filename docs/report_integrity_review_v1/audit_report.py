"""Local read-only report checks; never a Turnitin or authorship certification."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DOCX = ROOT / 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report.docx'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'


def visible_text(node):
    return ''.join(t.text or '' for t in node.findall('.//w:t', NS))


def tokens(text):
    return re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', text).casefold(), flags=re.UNICODE)


def matched_spans(report, source, size=12):
    index = defaultdict(list)
    for j in range(len(source) - size + 1):
        index[tuple(source[j:j+size])].append(j)
    spans = []
    i = 0
    while i <= len(report) - size:
        best = 0
        for j in index.get(tuple(report[i:i+size]), []):
            n = size
            while i+n < len(report) and j+n < len(source) and report[i+n] == source[j+n]:
                n += 1
            best = max(best, n)
        if best:
            spans.append({'report_token_start': i, 'length_words': best,
                          'report_excerpt': ' '.join(report[i:i+min(best, 30)])})
            i += best
        else:
            i += 1
    return spans


before = hashlib.sha256(DOCX.read_bytes()).hexdigest()
with ZipFile(DOCX) as archive:
    xml = ET.fromstring(archive.read('word/document.xml'))
    parents = {child: parent for parent in xml.iter() for child in parent}
    all_text = visible_text(xml)
    main = False
    references = False
    front, body, reference_entries = [], [], []
    body_heading_count = 0
    for paragraph in xml.findall('.//w:p', NS):
        text = visible_text(paragraph)
        style_node = paragraph.find('w:pPr/w:pStyle', NS)
        style = style_node.get(W+'val') if style_node is not None else 'Normal'
        if style == 'Heading1' and text.startswith('1 INTRODUCTION'):
            main = True
        if style == 'Heading1' and text == 'REFERENCES':
            references = True
        if main and not references and style == 'Heading1':
            body_heading_count += 1
        if not main:
            front.append(text)
        elif not references:
            body.append(text)
        if references and re.match(r'^\[\d+\]', text):
            reference_entries.append(text)
    body_tokens = tokens('\n'.join(body))
    front_tokens = tokens('\n'.join(front))
    assert main and references and body_heading_count == 8, 'Chapter/reference boundaries were not identified.'
    assert len(body_tokens) > 1000, 'Technical comparison corpus is unexpectedly short.'
    suspicious_codepoints = [0x200b, 0x200c, 0x200d, 0x2060, 0xfeff,
                             *range(0x202a, 0x202f), *range(0x2066, 0x206a)]
    suspicious = {f'U+{c:04X} {unicodedata.name(chr(c), "UNKNOWN")}': all_text.count(chr(c))
                  for c in suspicious_codepoints if chr(c) in all_text}
    hidden_runs, web_hidden_runs = [], []
    for run in xml.findall('.//w:r', NS):
        value = visible_text(run)
        enabled = lambda tag: run.find('w:rPr/w:'+tag, NS) is not None and run.find('w:rPr/w:'+tag, NS).get(W+'val', 'true') not in ('0','false','off')
        if enabled('vanish') and value.strip():
            hidden_runs.append(value)
        if enabled('webHidden'):
            ancestor = parents.get(run)
            while ancestor is not None and ancestor.tag != W+'p':
                ancestor = parents.get(ancestor)
            style_node = ancestor.find('w:pPr/w:pStyle', NS) if ancestor is not None else None
            style = style_node.get(W+'val') if style_node is not None else 'Normal'
            web_hidden_runs.append({'style': style, 'text': value,
                                    'field': ' '.join(x.text or '' for x in run.findall('w:instrText', NS))})
    nonempty_web = [r for r in web_hidden_runs if r['text'].strip()]
    nav_styles = {'TOC1','TOC2','TableofFigures'}
    unexpected_web = [r for r in nonempty_web if r['style'] not in nav_styles or not r['text'].strip().isdigit()]

result = {
    'review_date': '2026-11-22',
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'report': DOCX.relative_to(ROOT).as_posix(),
    'report_sha256': before,
    'mode': 'Read-only local document inspection and bounded corpus comparison.',
    'turnitin_used': False, 'turnitin_similarity_score': None, 'turnitin_ai_score': None,
    'department_requires_both_scores': True, 'department_similarity_cutoff': None,
    'department_ai_cutoff': None,
    'characters': {
        'selected_zero_width_or_bidi_counts': suspicious,
        'cyrillic_characters': sum('CYRILLIC' in unicodedata.name(c, '') for c in all_text),
        'normal_non_ascii_characters': [{'codepoint': f'U+{ord(c):04X}', 'name': unicodedata.name(c, 'UNKNOWN'), 'count': n}
                                        for c,n in Counter(all_text).items() if ord(c)>127],
        'explicit_vanish_text_runs': len(hidden_runs),
        'word_web_hidden_run_markers': len(web_hidden_runs),
        'web_hidden_numeric_navigation_results': len(nonempty_web),
        'web_hidden_numeric_results_by_style': dict(Counter(r['style'] for r in nonempty_web)),
        'web_hidden_page_reference_field_codes': sum('PAGEREF' in r['field'] for r in web_hidden_runs),
        'unexpected_non_navigation_web_hidden_text': unexpected_web,
        'scope_limit': 'Selected Unicode characters and direct run properties; not an exhaustive document-forensics or statistical-watermark test.'
    },
    'local_overlap_method': 'Casefolded NFKC Unicode word tokens, punctuation ignored, exact contiguous matches of at least 12 words. No semantic paraphrase or web-wide search.',
    'comparison_scope': {'technical_chapters': body_heading_count,
                         'technical_word_tokens': len(body_tokens),
                         'front_matter_word_tokens': len(front_tokens),
                         'exclusions': 'References, appendices, headers/footers, math-only elements and image text are outside this text-overlap comparison.'},
    'citation_inventory': {'numbered_reference_entries': len(reference_entries),
                           'claim_by_claim_source_verification_complete': False,
                           'note': 'An entry count does not establish citation accuracy, complete attribution or support for every claim.'},
    'local_comparisons': [],
    'limitations': ['Not a Turnitin similarity percentage or an AI-writing determination.',
                    'Only the two supplied senior PDFs are in this comparison corpus; publisher/student/web databases are not searched.',
                    'Front matter includes standard institutional/degree/certificate language. A shared span is not automatically plagiarism.',
                    'No watermark detector, hidden-character bypass, external checker upload, new model training or dependency installation was used.']
}
pdf_dir = ROOT.parent
for filename in ['B.Tech Project Report (Siddharth Yash).pdf',
                 'Minor Project Report 2K20_IT_52 2K20_IT_49 2K20_IT_59.pdf']:
    pdf_path = pdf_dir/filename
    if not pdf_path.exists():
        result['local_comparisons'].append({'source': filename, 'available': False})
        continue
    with pymupdf.open(pdf_path) as pdf:
        source_text = '\n'.join(page.get_text() for page in pdf)
        source_tokens = tokens(source_text)
    fm = matched_spans(tokens('\n'.join(front)), source_tokens)
    bm = matched_spans(tokens('\n'.join(body)), source_tokens)
    result['local_comparisons'].append({
        'source': filename, 'available': True,
        'source_sha256': hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        'front_matter_exact_spans_at_least_12_words': fm,
        'technical_chapters_exact_spans_at_least_12_words': bm,
        'technical_longest_qualifying_match_words': max((s['length_words'] for s in bm), default=0),
        'note': 'No overall similarity percentage is computed; these are bounded local matches only.'
    })
after = hashlib.sha256(DOCX.read_bytes()).hexdigest()
assert before == after, 'Report changed during audit; preserve and investigate.'
result['report_preserved'] = True
(OUT/'local_audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(json.dumps({
    'report_preserved': True,
    'selected_invisible_codepoints': suspicious,
    'cyrillic_characters': result['characters']['cyrillic_characters'],
    'vanish_text_runs': len(hidden_runs),
    'web_hidden_navigation_numeric_results': len(nonempty_web),
    'unexpected_web_hidden_text': len(unexpected_web),
    'comparisons': [{ 'source': x['source'], 'available': x['available'],
                     'front_matches': len(x.get('front_matter_exact_spans_at_least_12_words', [])),
                     'body_matches': len(x.get('technical_chapters_exact_spans_at_least_12_words', []))}
                    for x in result['local_comparisons']],
    'turnitin_similarity_score': None, 'turnitin_ai_score': None
}, indent=2))
