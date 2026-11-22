"""Record editorial changes against the pinned, already-reviewed report."""
import hashlib, io, json, subprocess
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REV = '297c0a421771e93c02b022c73222c9bcc3385bd7'
PATH = 'output/docx/SAFE_Pipe_DTU_Minor_Project_Report_Reviewed.docx'
data = subprocess.check_output(['git', 'show', REV+':'+PATH], cwd=ROOT)
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(io.BytesIO(data)) as z:
    root = E.fromstring(z.read('word/document.xml'))
paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in root.findall('.//w:body/w:p', ns)]
edits = []
def original(prefix):
    matches = [p for p in paragraphs if p.startswith(prefix)]
    assert len(matches) == 1, prefix
    return matches[0]
def replace(prefix, new):
    edits.append({'before':original(prefix), 'after':new})
def cite(prefix, number):
    old = original(prefix)
    replace(prefix, old.replace('[7]', f'[{number}]') if '[7]' in old else old.rstrip('. ')+f' [{number}].')

replace('Conformal prediction provides', 'Conformal prediction calibrates prediction sets or bounds using held-out scores. Its usual marginal coverage argument requires exchangeability of calibration and future scores [5]. SAFE-Pipe computes one maximum residual score per family/configuration group. Keeping repeats together prevents repeat leakage, but does not establish exchangeability across the fixed groups, new profiles or different hardware. The nominal level is therefore reported alongside observed coverage; it is not a selected-job success probability [8].')
replace('LightGBM predicts log successful', 'LightGBM fits log successful engine runtime with 120 trees, seven leaves, learning rate 0.05, minimum child count three, L2 penalty one, seed 2026 and one training thread. Family and configuration ID are one-hot encoded. Calibration takes the maximum log residual per family/configuration group. With 12 groups and alpha 0.1, the finite-sample rank selects the largest score. The stored log offset 0.523642 gives U = t * exp(0.523642), approximately 1.688 * t [8].')
replace('The saved artifact contains', 'LightGBM is the fixed tabular regression model. The recorded comparison uses a family-median baseline, not alternative learned models. No archived tuning or sensitivity study establishes the 120-tree/seven-leaf settings as optimal, and no iteration-wise training history was retained. Figures 5 and 6 use saved held-out predictions without retraining [8, 9].')
replace('The latest original-advisor implementation,', original('The latest original-advisor implementation,').removesuffix(' [7]')+' [14]\nA concrete Windows compatibility issue concerned line endings in the saved LightGBM text model. Git CRLF conversion could invalidate stored tree-byte offsets. The loader reads the model as text with newline normalization, and dedicated regression tests cover the Windows-compatible loading path [8].')
for prefix, number in [('The grouped split keeps',8), ('The saved test set contains',9), ('The stored upper estimates covered',9), ('Stage A recorded',10), ('Stage B recorded',11), ('The existing export preserves',12), ('The earlier development screen retained',15), ('The existing one-probe development replay',13)]:
    cite(prefix, number)
replace('The file docs/minor_report_v1/source_manifest.json', 'The report input manifest pins compact evidence files to the original-advisor and research revisions, with LF-normalized SHA-256 hashes. The historical Windows verification receipt identifies 78 source/evidence files at its checkpoint; those identities are not a claim that every later source file remains byte-identical [14]. Tables and plots are traceable to retained evidence and generation scripts. Original Parquet inputs and full raw JSONL diagnostics are outside the shareable pack. Repeating physical measurements additionally requires those retained files, their recorded environment and the experiment host; a fresh independent rerun has not been performed. The memory export preserves worker lifetimes and missing-value distinctions [12].')
replace('The original model is supported', 'The original model is supported by only four fixed profiles, and its test contains eight family/configuration groups. Research uses one generation seed and shared samples. Runtime repeats are not independent new workloads; grouping them does not establish exchangeability across calibration and future workloads. The model settings and balanced weights were not shown to be optimal by a sensitivity study. Some costs are historical replays, not online executions, and resource terms are configured proxies. Worker death and snapshot timing can censor telemetry. These records do not establish cross-machine generalization, AWS Glue performance, multi-node performance, a calibrated failure classifier or a generally superior selector.')
main = 'caa8a8a919d7cf4822e1735c795d22c31b63dc71'
research = 'edef1cdbba0d980bc1a359960d7339cc08d13d84'
refs = [
    (8,main,'experiments/train_runtime.py','Training settings and grouped calibration; see also safe_pipe/models/runtime.py and tests/test_runtime_model.py at this revision'),
    (9,main,'artifacts/main_v1/runtime_test_predictions.csv','Saved held-out runtime predictions; metrics in runtime_metrics.json in the same directory'),
    (10,research,'reports/research_stage_a_windows_v1/summary.json','Stage A full-input results; plan and measurements in the same directory'),
    (11,research,'reports/research_stage_b_windows_v1/summary.json','Stage B paired pressure comparisons; plan and measurements in the same directory'),
    (12,research,'reports/worker_memory_stage_a_b_v1/workers.json','Worker-lifetime memory export; interpretation in reports/worker_memory_review_20261116/analysis.json'),
    (13,research,'reports/one_probe_feasibility_20261116/analysis.json','Historical one-probe feasibility replay'),
    (14,main,'reports/main_validation_windows_checks_v1/verification.json','Original-advisor Windows verification receipt'),
    (15,research,'reports/research_screen_review_20261114/analysis.json','Earlier probe-ranking screen analysis')]
plan = {'version':'report-evidence-v2', 'date':'2026-11-22', 'base_revision':REV, 'base_path':PATH,
        'base_sha256':hashlib.sha256(data).hexdigest(), 'edits':edits,
        'references':[f'[{n}] SAFE-Pipe project team, {title}, revision {rev[:7]}, 2026. https://github.com/Aggdaksh/SAFE-Pipe1/blob/{rev}/{path}' for n,rev,path,title in refs],
        'reference_insert_before':'APPENDIX A SAVED ADVISOR OUTPUT',
        'evidence_links':[{'number':n,'revision':rev,'path':path} for n,rev,path,title in refs],
        'scope':'Editorial corrections and evidence locators; no new experimental results. Base includes all earlier edits and disclosure.'}
(HERE/'evidence_revision_plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(f'Prepared {len(edits)} paragraph changes and {len(refs)} direct artifact references.')
