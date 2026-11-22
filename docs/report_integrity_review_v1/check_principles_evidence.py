"""Recompute selected report facts without fitting models or executing jobs."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
doc = ROOT/'output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx'
manifest = json.loads((ROOT/'docs/minor_report_v1/source_manifest.json').read_text())
for entry in manifest['inputs']:
    data = subprocess.check_output(['git', 'show', entry['revision']+':'+entry['path']], cwd=ROOT)
    assert hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest() == entry['sha256_lf'], entry['path']
with (ROOT/'artifacts/main_v1/runtime_test_predictions.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
def mdape(column):
    return 100*statistics.median(abs(float(r[column])-float(r['engine_seconds']))/float(r['engine_seconds']) for r in rows)
advice = json.loads((ROOT/'docs/minor_report_v1/advisor_capture/sort_balanced.json').read_text())
candidates = advice['candidates']
assert len(candidates) == 8 and all(c['eligible'] and c['runtime_upper_s'] <= 13.1 for c in candidates)
assert min(candidates, key=lambda c: c['score'])['config_id'] == 'w2_t2_1g'
receipt = json.loads((ROOT/'reports/main_validation_windows_checks_v1/verification.json').read_text())
for path, expected in receipt['source_sha256_lf'].items():
    assert hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == expected, path
evidence = {
    'date':'2026-11-22', 'reviewed_docx_sha256':hashlib.sha256(doc.read_bytes()).hexdigest(),
    'pinned_source_hashes_verified':len(manifest['inputs']),
    'original_verification_hashes_verified':len(receipt['source_sha256_lf']),
    'recomputed_test_mdape_percent':mdape('predicted_seconds'),
    'recomputed_baseline_mdape_percent':mdape('median_baseline_seconds'),
    'test_rows':len(rows), 'test_groups':len({(r['family'],r['config_id']) for r in rows}),
    'upper_covered_rows':sum(float(r['engine_seconds']) <= float(r['upper_seconds']) for r in rows),
    'figure_4_eligible_candidates':8, 'figure_4_lowest_score_config':'w2_t2_1g',
    'software_suite_rerun':False, 'benchmark_or_training_run':False,
    'raw_parquet_and_jsonl_reaudited':False,
    'scope':'Read-only saved DOCX, main training/encoding/advisor code, selected requirement-oriented tests, report production scripts, decision records, pinned evidence and cited primary literature. Not an exhaustive codebase or raw-record audit.'}
(HERE/'principles_evidence.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
print(json.dumps(evidence, indent=2))
