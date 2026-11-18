"""Build the offline Hinglish learning guide from reviewed, local translations.

This is document generation only. It imports no project runner/model and reads
the English guide plus its translation file. Existing scientific records stay untouched.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ENGLISH = ROOT / "SAFE_PIPE_LEARNING_GUIDE.html"
HINGLISH = ROOT / "SAFE_PIPE_LEARNING_GUIDE_HINGLISH.html"
TRANSLATIONS = ROOT / "docs/learning_guide_hinglish_translations.json"


def translate_indexed(html, tag, translations):
    pattern = re.compile(fr"(<{tag}\b[^>]*>)([\s\S]*?)(</{tag}>)")
    matches = list(pattern.finditer(html))
    if isinstance(translations, list):
        if len(matches) != len(translations):
            raise ValueError(f"English {tag} blocks changed; review the translations")
        translations = dict(enumerate(translations))
    else:
        translations = {int(k): v for k, v in translations.items()}
    if any(index >= len(matches) for index in translations):
        raise ValueError(f"Missing source {tag} block")
    index = -1

    def replace(match):
        nonlocal index
        index += 1
        return match[1] + translations.get(index, match[2]) + match[3]

    return pattern.sub(replace, html)


def build():
    source = ENGLISH.read_text(encoding="utf-8")
    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    marker = '<script id="guide-data" type="application/json">'
    body, scripts = source.split(marker, 1)
    # Existing inline code IDs, equations, figures and numeric cells must survive.
    original_code = re.findall(r"<code>([\s\S]*?)</code>", body)
    original_figures = re.findall(r"<svg\b[\s\S]*?</svg>", body)
    original_formulas = re.findall(r'<div class="formula">([\s\S]*?)</div>', body)
    paragraph_matches = list(re.finditer(r"<p\b[^>]*>([\s\S]*?)</p>", body))
    needed = {str(i) for i, match in enumerate(paragraph_matches)
              if 'class="source"' not in match[0] and i not in (0, 37, 39)}
    if set(translations["p"]) != needed:
        raise ValueError("English paragraphs changed; review paragraph coverage")
    for tag in ("p", "h1", "h2", "h3", "li", "summary", "figcaption", "td"):
        body = translate_indexed(body, tag, translations[tag])
    callouts = translations["callouts"]
    pattern = re.compile(r'(<div class="callout[^\"]*">)([\s\S]*?)(</div>)')
    if len(pattern.findall(body)) != len(callouts):
        raise ValueError("Callout count changed")
    iterator = iter(callouts)
    body = pattern.sub(lambda match: match[1] + next(iterator) + match[3], body)
    pattern = re.compile(r'(<a href="#[^\"]+">)([^<]*)(</a>)')
    if len(pattern.findall(body)) != len(translations["nav"]):
        raise ValueError("Chapter navigation changed")
    iterator = iter(translations["nav"])
    body = pattern.sub(lambda match: match[1] + next(iterator) + match[3], body)
    labels = translations["text"]

    def label(match):
        text = match[0]
        key = text.strip()
        return text.replace(key, labels[key], 1) if key in labels else text

    body = re.sub(r"(?<=>)([^<>]+)(?=<)", label, body)
    body = body.replace('<html lang="en">', '<html lang="hi-Latn">')
    body = body.replace("Understanding SAFE-Pipe · A visual learning guide", "SAFE-Pipe samjho · Puri Hinglish visual guide")
    body = body.replace("A complete, beginner-friendly visual guide to SAFE-Pipe: its original advisor, experiments, metrics, research findings and current status.",
                        "SAFE-Pipe ki detailed Hinglish guide: basics, midterm, LightGBM, actual metrics, research journey aur current status.")
    body = body.replace('aria-label="Guide navigation"', 'aria-label="Guide ke chapters"')
    body = body.replace('aria-label="Find a chapter" placeholder="Find a chapter…"',
                        'aria-label="Chapter dhoondo" placeholder="Chapter dhoondo…"')
    switch = '<a class="button" href="SAFE_PIPE_LEARNING_GUIDE.html" lang="en" style="display:inline-block;margin-bottom:14px">Read in English →</a>\n '
    body = re.sub(r'<a class="button language-switch"[^>]*>.*?</a>\s*', '', body)
    body = body.replace('<input class="nav-search"', switch + '<input class="nav-search"', 1)
    body = re.sub(r'<footer class="footer">[\s\S]*?</footer>',
                  '<footer class="footer">SAFE-Pipe · Hinglish understanding guide · Evidence snapshot 7f9c1b0 · 18 November 2026<br>Present karte waqt original advisor, development experiments, historical replays aur software tests ko alag rakho.</footer>', body)
    # Translate presentation strings only; math, selectors, enums and data stay intact.
    payload, code = scripts.split('</script>', 1)
    changes = {
        "Enter a positive actual runtime and a non-negative predicted runtime.": "Actual runtime positive aur predicted runtime zero ya positive enter karo.",
        "% absolute percentage error.": "% absolute percentage error. Ye runtime ki prediction error hai.",
        "fact sample at a ": "fact sample, full target ",
        " GB full target → ": " GB → ",
        " MB) per worker. Two workers: ": " MB) har worker. Two workers ka total: ",
        " MB configured in total. This is not the measured working set.": " MB configured. Ye measured working set nahi hai.",
        "Enter a positive engine deadline.": "Engine deadline positive enter karo.",
        "Upper exceeds deadline": "Upper deadline se zyada hai",
        "Over memory budget": "Memory budget se zyada hai",
        "Input guard": "Input guard reject karta hai",
        "Saved-prediction replay selects ": "Saved-prediction replay ki choice: ",
        " candidates eligible. No job is executed.": " candidates eligible hain. Koi job execute nahi hoti.",
        "Abstain: no saved candidate passes the displayed deadline/budget checks. No job is executed.": "Abstain: koi saved candidate is deadline/budget ko pass nahi karta. Koi job execute nahi hoti.",
        "Eligible · selected": "Eligible · select hua",
        "'Close answers'": "'Answers band karo'",
        "'Open answers'": "'Answers kholo'",
        "/5 correct; ": "/5 sahi; ",
        "/5 answered. These are learning checks, not a SAFE-Pipe model metric. Read the explanations above.": "/5 answer kiye. Ye learning check hai, SAFE-Pipe model ki metric nahi. Upar explanations padho.",
    }
    for english, hinglish in changes.items():
        if english not in code:
            raise ValueError(f"Interactive text changed: {english}")
        code = code.replace(english, hinglish)
    if re.findall(r"<code>([\s\S]*?)</code>", body) != original_code:
        raise ValueError("A technical identifier was changed")
    if re.findall(r"<svg\b[\s\S]*?</svg>", body) != original_figures:
        raise ValueError("A source figure was changed")
    if re.findall(r'<div class="formula">([\s\S]*?)</div>', body) != original_formulas:
        raise ValueError("A source formula was changed")
    HINGLISH.write_text(body + marker + payload + '</script>' + code, encoding="utf-8")
    print(json.dumps({"output": HINGLISH.name, "chapters": len(translations["nav"]),
                      "translated_paragraphs": len(translations["p"]), "figures_preserved": len(original_figures),
                      "formulas_preserved": len(original_formulas), "inline_data_unchanged": True}))


if __name__ == "__main__":
    build()
