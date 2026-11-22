"""Apply a versioned editorial plan to a pinned Word template, without experiments."""
import argparse, hashlib, io, json, re, subprocess
from pathlib import Path
from xml.dom import minidom
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def text(node):
    return ''.join(t.firstChild.data if t.firstChild else '' for t in node.getElementsByTagNameNS(W, 't'))

def set_text(paragraph, value):
    # Only edit plain prose; retain paragraph/run formatting and all other parts.
    run_props = paragraph.getElementsByTagNameNS(W, 'rPr')
    saved = run_props[0].cloneNode(True) if run_props else None
    for node in list(paragraph.childNodes):
        if node.nodeType != node.ELEMENT_NODE or node.localName != 'pPr':
            paragraph.removeChild(node)
    run = paragraph.ownerDocument.createElementNS(W, 'w:r')
    if saved:
        run.appendChild(saved)
    t = paragraph.ownerDocument.createElementNS(W, 'w:t')
    t.setAttribute('xml:space', 'preserve')
    t.appendChild(paragraph.ownerDocument.createTextNode(value))
    run.appendChild(t); paragraph.appendChild(run)

def build(output):
    if output.exists():
        raise FileExistsError(f'Preserve existing output; choose a new path: {output}')
    plan = json.loads((HERE/'evidence_revision_plan.json').read_text(encoding='utf-8'))
    data = subprocess.check_output(['git', 'show', plan['base_revision']+':'+plan['base_path']], cwd=ROOT)
    if hashlib.sha256(data).hexdigest() != plan['base_sha256']:
        raise ValueError('Pinned template hash mismatch')
    with ZipFile(io.BytesIO(data)) as archive:
        document = minidom.parseString(archive.read('word/document.xml'))
        body = document.getElementsByTagNameNS(W, 'body')[0]
        paragraphs = [n for n in body.childNodes if n.nodeType == n.ELEMENT_NODE and n.localName == 'p']
        for edit in plan['edits']:
            matches = [p for p in paragraphs if text(p) == edit['before']]
            if len(matches) != 1:
                raise ValueError('Expected one source paragraph: '+edit['before'][:80])
            paragraph = matches[0]
            segments = edit['after'].split('\n')
            template = paragraph.cloneNode(True)
            set_text(paragraph, segments[0])
            for segment in segments[1:]:
                new = template.cloneNode(True); set_text(new, segment)
                body.insertBefore(new, paragraph.nextSibling); paragraph = new
        reference = next(p for p in paragraphs if text(p).startswith('[7] SAFE-Pipe project team'))
        for value in plan['references']:
            new = reference.cloneNode(True); set_text(new, value)
            props = new.getElementsByTagNameNS(W, 'pPr')[0]
            if not props.getElementsByTagNameNS(W, 'keepLines'):
                props.appendChild(document.createElementNS(W, 'w:keepLines'))
            body.insertBefore(new, reference.nextSibling); reference = new
        # Compact, consistent bibliography typography keeps each entry together.
        for paragraph in body.getElementsByTagNameNS(W, 'p'):
            if not re.match(r'^\[\d+\] ', text(paragraph)):
                continue
            props = paragraph.getElementsByTagNameNS(W, 'pPr')[0]
            for tag in ['keepLines', 'spacing']:
                for node in list(props.getElementsByTagNameNS(W, tag)):
                    props.removeChild(node)
            props.appendChild(document.createElementNS(W, 'w:keepLines'))
            spacing = document.createElementNS(W, 'w:spacing')
            for key, value in [('line','240'),('lineRule','auto'),('after','120')]:
                spacing.setAttribute('w:'+key, value)
            props.appendChild(spacing)
            for run in paragraph.getElementsByTagNameNS(W, 'r'):
                nodes = run.getElementsByTagNameNS(W, 'rPr')
                rp = nodes[0] if nodes else document.createElementNS(W, 'w:rPr')
                if not nodes:
                    run.insertBefore(rp, run.firstChild)
                for tag in ['sz','szCs']:
                    for node in list(rp.getElementsByTagNameNS(W, tag)):
                        rp.removeChild(node)
                    size = document.createElementNS(W, 'w:'+tag); size.setAttribute('w:val','22'); rp.appendChild(size)
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, 'w') as result:
            for member in archive.infolist():
                result.writestr(member, document.toxml(encoding='utf-8') if member.filename == 'word/document.xml' else archive.read(member.filename))
    print(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    build(parser.parse_args().out.resolve())
