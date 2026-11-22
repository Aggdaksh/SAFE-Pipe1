"""Build report illustrations from pinned, existing evidence only.

Run with the system Python that has matplotlib/numpy installed. This script does
not import project experiment runners, generate datasets, fit models or run Dask.
It captures inference-only CLI examples with the original .venv, once per case.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path
import statistics as stats
import subprocess
import sys
import textwrap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRATCH = ROOT / "reports/_scratch/minor_report_v1"
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(SCRATCH / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

MAIN = "caa8a8a919d7cf4822e1735c795d22c31b63dc71"
RESEARCH = "edef1cdbba0d980bc1a359960d7339cc08d13d84"
DATE = "2026-11-21"
FIG = HERE / "figures"
TABLE = HERE / "tables"
CAPTURE = HERE / "advisor_capture"
for directory in (FIG, TABLE, CAPTURE):
    directory.mkdir(exist_ok=True)
manifest = {"date": DATE, "original_advisor_evidence_revision": MAIN,
            "research_evidence_revision": RESEARCH, "inputs": [],
            "scope": "Read-only evidence analysis, inference-only CLI captures and report figures; no fresh benchmarks or training."}
figures = []
BLUE, TEAL, GOLD, RED, INK = "#2563a6", "#087f8c", "#c48a16", "#ba4550", "#142b43"
COLORS = [BLUE, TEAL, GOLD, RED]
FAMILIES = ["scan_filter", "groupby", "skewed_join", "sort_merge"]
NAMES = {"scan_filter": "Scan/filter", "groupby": "Group-by", "skewed_join": "Skewed join", "sort_merge": "Key shuffle (sort_merge)"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelcolor": INK, "text.color": INK,
                     "axes.titleweight": "bold", "svg.fonttype": "none",
                     "figure.facecolor": "white", "savefig.facecolor": "white"})


def source(path, revision=MAIN, kind="json"):
    data = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    manifest["inputs"].append({"path": path, "revision": revision,
                              "sha256_lf": hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()})
    text = data.decode("utf-8-sig")
    return json.loads(text) if kind == "json" else list(csv.DictReader(io.StringIO(text)))


def export_csv(name, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f"Empty table: {name}")
    with (TABLE / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def save(fig, key, title, caption, sources, section="Results"):
    # Keep chart text readable when reduced to A4 report width.
    for artist in fig.findobj(matplotlib.text.Text):
        if artist.get_fontsize() < 13:
            artist.set_fontsize(13)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in fig.findobj(matplotlib.text.Text):
        bounds = getattr(artist, "_report_box", None)
        if bounds is None:
            continue
        axis, width, height = bounds
        max_width = axis.bbox.width * width * .91
        max_height = axis.bbox.height * height * .90
        font = artist.get_fontproperties()
        lines = []
        for paragraph in artist.get_text().split("\n"):
            line = ""
            for word in paragraph.split():
                proposal = (line + " " + word).strip()
                if line and renderer.get_text_width_height_descent(proposal, font, False)[0] > max_width:
                    lines.append(line); line = word
                else:
                    line = proposal
            lines.append(line)
        artist.set_text("\n".join(lines))
        fig.canvas.draw()
        while (artist.get_window_extent(renderer).width > max_width or artist.get_window_extent(renderer).height > max_height) and artist.get_fontsize() > 10:
            artist.set_fontsize(artist.get_fontsize() - .5)
            fig.canvas.draw()
    fig.savefig(FIG / f"{key}.png", dpi=240, bbox_inches="tight", pad_inches=.2)
    fig.savefig(FIG / f"{key}.svg", bbox_inches="tight", pad_inches=.2)
    svg = FIG / f"{key}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)
    figures.append({"id": key, "title": title, "caption": caption,
                    "sources": sources, "section": section})


def box(ax, xy, width, height, text, color=BLUE):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.012",
                               facecolor=color + "12", edgecolor=color, linewidth=1.3))
    artist = ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=13)
    artist._report_box = (ax, width, height)


def arrow(ax, start, end, color=INK):
    ax.annotate("", xy=end, xytext=start,
                arrowprops={"arrowstyle": "->", "color": color, "lw": 1.5})


def source_check():
    receipt = json.loads((ROOT / "reports/main_validation_windows_checks_v1/verification.json").read_text())
    for path, expected in receipt["source_sha256_lf"].items():
        actual = hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected:
            raise ValueError(f"Verified original evidence changed: {path}")
    return receipt


receipt = source_check()
runs = source("data/curated/runs.csv", kind="csv")
pred = source("artifacts/main_v1/runtime_test_predictions.csv", kind="csv")
metrics = source("artifacts/main_v1/runtime_metrics.json")
datasets = source("configs/datasets_main_v1.json")
grid = source("configs/dask_grid.json")["configs"]
split = source("configs/model_split_main_v1.json")
policy = source("reports/policy_metrics.json")
stage_a = source("reports/research_stage_a_windows_v1/summary.json", RESEARCH)
stage_b = source("reports/research_stage_b_windows_v1/summary.json", RESEARCH)
feasible = source("reports/one_probe_feasibility_20261116/analysis.json", RESEARCH)
workers = source("reports/worker_memory_stage_a_b_v1/workers.json", RESEARCH)
memory_review = source("reports/worker_memory_review_20261116/analysis.json", RESEARCH)
screen = source("reports/research_screen_review_20261114/analysis.json", RESEARCH)
one_probe_checks = source("reports/one_probe_windows_checks_v1/verification.json", RESEARCH)
source("docs/report_blueprint_evidence.json", RESEARCH)
source("reports/main_validation_windows_checks_v1/verification.json")

assert len(runs) == 96 and all(r["status"] == "success" for r in runs)
assert len(pred) == 24 and len({(r["family"], r["config_id"]) for r in pred}) == 8
model_mdape = 100 * stats.median(abs(float(r["predicted_seconds"]) - float(r["engine_seconds"])) / float(r["engine_seconds"]) for r in pred)
baseline_mdape = 100 * stats.median(abs(float(r["median_baseline_seconds"]) - float(r["engine_seconds"])) / float(r["engine_seconds"]) for r in pred)
assert abs(model_mdape - metrics["test_mdape_percent"]) < 1e-10
assert abs(baseline_mdape - metrics["median_baseline_test_mdape_percent"]) < 1e-10
covered = sum(float(r["engine_seconds"]) <= float(r["upper_seconds"]) for r in pred)
assert covered == 24
assert feasible["current_admission_enabled"] is False

# Capture actual inference output, without invoking an execution or generation path.
capture_index = []
for label, args in [
    ("sort_balanced", ["--family", "sort_merge", "--sla", "13.1"]),
    ("sort_resource", ["--family", "sort_merge", "--sla", "13.1", "--mode", "resource"]),
    ("sort_fastest", ["--family", "sort_merge", "--sla", "13.1", "--mode", "fastest"]),
    ("sort_abstain", ["--family", "sort_merge", "--sla", "0.01"]),
]:
    path = CAPTURE / f"{label}.json"
    command = [str(ROOT / ".venv/Scripts/python.exe"), "-m", "safe_pipe.cli", "advise", *args]
    if not path.exists():
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
        if completed.returncode:
            (CAPTURE / f"{label}.failure.txt").write_bytes(completed.stdout + completed.stderr)
            raise RuntimeError(f"CLI capture failed: {label}; exit {completed.returncode}")
        json.loads(completed.stdout)
        path.write_bytes(completed.stdout)
        (CAPTURE / f"{label}.stderr.txt").write_bytes(completed.stderr)
    capture_index.append({"case": label, "argv": command, "stdout": path.name,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "scope": "Inference only; no Dask execution or model fitting."})
(CAPTURE / "commands.json").write_text(json.dumps(capture_index, indent=2) + "\n")
advisor = json.loads((CAPTURE / "sort_balanced.json").read_text())

# F01: current implementation, with prospective execution and research separated.
fig, ax = plt.subplots(figsize=(11.2, 6.2)); ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
ax.text(.02, .97, "Historical fitting and current advice are separate paths", fontsize=15, weight="bold")
for x, text in [(.02, "Frozen datasets\n4 profiles"), (.27, "Measured table\n96 original jobs"),
                (.52, "Grouped fitting\n+ calibration"), (.77, "Saved model\n+ support bindings")]:
    box(ax, (x, .67), .20, .18, text)
for x in [.22, .47, .72]: arrow(ax, (x, .76), (x + .05, .76))
for x, text in [(.02, "Workload metadata\n+ deadline/preferences"), (.27, "Check support\nPredict 8 candidates"),
                (.52, "Eligibility + score\nSelect or abstain"), (.77, "Explained JSON\nCandidate comparisons")]:
    box(ax, (x, .35), .20, .18, text, TEAL)
for x in [.22, .47, .72]: arrow(ax, (x, .44), (x + .05, .44), TEAL)
arrow(ax, (.87, .67), (.37, .53))
box(ax, (.02, .04), .45, .17, "Separate research branch: pressure/probe diagnosis\nAdmission disabled; not the deployed advisor", GOLD)
box(ax, (.53, .04), .44, .17, "Fresh validation infrastructure: software verified\nStudy preparation/collection await review", RED)
save(fig, "F01_architecture", "System architecture and evidence boundaries",
     "Schematic of the original offline data/model path and the current inference-only advisor. Advice does not launch a job. Fresh validation infrastructure is software-verified; its study has not been prepared or collected. The research decision prototype remains separate and disabled.",
     ["safe_pipe/advisor.py", "docs/CONFIG_SELECTION.md", "docs/MAIN_COMPLETION_PLAN.md"], "Architecture")

# F02: eight configurations and original study dimensions.
fig, ax = plt.subplots(figsize=(11.2, 4.8)); ax.axis("off")
rows = [[c["config_id"], c["n_workers"], c["threads_per_worker"], c["memory_limit"],
         c["n_workers"] * c["threads_per_worker"], f"{c['n_workers'] * int(c['memory_limit'][0])} GB"] for c in grid]
table = ax.table(cellText=rows, colLabels=["Configuration", "Workers", "Threads/worker", "Cap/worker", "Total threads", "Total cap"], loc="center", cellLoc="center")
table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.8)
for (r, c), cell in table.get_celld().items():
    cell.set_edgecolor("#dce4eb")
    if r == 0: cell.set_facecolor(INK); cell.get_text().set_color("white")
    elif r % 2: cell.set_facecolor("#eef4f8")
ax.set_title("4 fixed workload profiles x 8 configurations x 3 repeats = 96 jobs", pad=20, fontsize=14)
save(fig, "F02_grid", "The bounded experiment grid", "The eight original candidates vary workers, threads per worker and decimal-GB memory caps. A 2 GB total cap can mean either one 2 GB worker or two 1 GB workers; these are different configurations. These caps are allocations, not measured peak usage. All three repetitions reuse each profile's fixed data.", ["configs/dask_grid.json", "data/curated/runs.csv"], "Methodology")
export_csv("configuration_grid", [dict(zip(["config_id", "workers", "threads_per_worker", "cap_per_worker", "total_threads", "total_cap"], r)) for r in rows])

# F03: physical input sizes and logical row counts, without conflating them.
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), layout="constrained")
for ax, key, div, xlabel in [(axes[0], "input_bytes", 1e6, "Compressed Parquet size (decimal MB)"), (axes[1], "n_rows", 1e6, "Declared rows (millions)")]:
    values = [d[key] / div for d in datasets]
    bars = ax.barh([NAMES[d["family"]] for d in datasets], values, color=COLORS)
    ax.bar_label(bars, fmt="%.2f", padding=4); ax.invert_yaxis(); ax.set_xlabel(xlabel); ax.set_xlim(0, max(values) * 1.24)
save(fig, "F03_datasets", "Four fixed original datasets", "The original study uses four synthetic datasets, one per workload profile. Disk size is compressed Parquet size, not the decompressed working set or peak RAM. Repeats do not generate new datasets; the later research inputs are a separate study.", ["configs/datasets_main_v1.json"], "Methodology")
export_csv("original_datasets", datasets)

# F04: original runtime medians plus repeat ranges.
runtime_groups = []
for family in FAMILIES:
    for c in grid:
        rr = [r for r in runs if r["family"] == family and r["config_id"] == c["config_id"]]
        assert len(rr) == 3
        values = [float(r["engine_seconds"]) for r in rr]
        runtime_groups.append({"family": family, "config_id": c["config_id"], "repeats": 3,
                               "median_seconds": stats.median(values), "minimum_seconds": min(values),
                               "maximum_seconds": max(values), "sla_seconds": float(rr[0]["sla_seconds"])})
export_csv("original_runtime_by_cell", runtime_groups)
fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.2), layout="constrained")
for ax, family, color in zip(axes.flat, FAMILIES, COLORS):
    values = [r for r in runtime_groups if r["family"] == family]
    med = np.array([r["median_seconds"] for r in values]); low = np.array([r["minimum_seconds"] for r in values]); high = np.array([r["maximum_seconds"] for r in values])
    ax.errorbar(med, np.arange(8), xerr=[med - low, high - med], fmt="o", color=color, capsize=3)
    ax.set_yticks(range(8), [r["config_id"] for r in values]); ax.invert_yaxis(); ax.set_xlim(left=0)
    ax.set_title(NAMES[family]); ax.set_xlabel("Engine runtime (seconds)"); ax.grid(axis="x", alpha=.15)
save(fig, "F04_runtime_ranges", "Measured engine runtime across the grid", "Each dot is the median of three original physical runs; bars show their minimum and maximum, not confidence intervals. Panels have independent horizontal scales. Engine timing excludes cluster startup and profiling. All 96 original runs succeeded; this chart does not predict future failure rates.", ["data/curated/runs.csv"], "Original results")

# F05: split membership is by group, not individual repeat.
fig, ax = plt.subplots(figsize=(11.2, 4.5)); ax.axis("off"); ax.set(xlim=(0, 1), ylim=(0, 1))
for x, title, detail, color in [(.02, "TRAIN", "12 groups / 36 rows\nFit the runtime model", BLUE), (.355, "CALIBRATE", "12 groups / 36 rows\nSet the upper multiplier", GOLD), (.69, "TEST", "8 groups / 24 rows\nReport held-out error", TEAL)]:
    box(ax, (x, .39), .29, .4, title + "\n\n" + detail, color)
ax.text(.5, .20, "Group = workload family + configuration; all 3 repeats stay together", ha="center", fontsize=12, weight="bold")
ax.text(.5, .06, "Four fixed workload profiles appear across these splits; this is not an unseen-workload test.", ha="center", fontsize=10)
save(fig, "F05_grouped_split", "Training, calibration and test separation", "The frozen split assigns 32 family/configuration groups to 12 training, 12 calibration and 8 test groups (36/36/24 rows). Repeats of a group never cross splits. This avoids repeat leakage but does not measure generalization to new workload profiles.", ["configs/model_split_main_v1.json", "reports/runtime_model.md"], "Methodology")
export_csv("grouped_split", [{"family": f, "config_id": c, "split": s, "rows": 3} for f, spec in split["families"].items() for s, ids in spec.items() for c in ids])

# F06: saved held-out predictions only; no inference or fitting for this plot.
fig, ax = plt.subplots(figsize=(8, 6.3), layout="constrained")
for family, color in zip(FAMILIES, COLORS):
    rr = [r for r in pred if r["family"] == family]
    ax.scatter([float(r["engine_seconds"]) for r in rr], [float(r["predicted_seconds"]) for r in rr], label=NAMES[family], color=color, s=42, alpha=.85)
maximum = max(max(float(r["engine_seconds"]), float(r["predicted_seconds"])) for r in pred) * 1.1
ax.plot([0, maximum], [0, maximum], color="#8392a1", linestyle="--", label="Perfect prediction")
ax.set(xlim=(0, maximum), ylim=(0, maximum), xlabel="Actual engine runtime (seconds)", ylabel="Predicted engine runtime (seconds)")
ax.legend(loc="upper left", fontsize=9); ax.grid(alpha=.15)
save(fig, "F06_prediction_scatter", "Held-out predicted versus actual runtime", "Each point is one saved held-out row: 24 repeat measurements belonging to eight family/configuration groups. The dashed line is perfect agreement. The model's held-out MdAPE is 13.84%; these points are not training accuracy and are not 24 independent workload profiles.", ["artifacts/main_v1/runtime_test_predictions.csv"], "Original results")

# F07: recomputed median absolute percentage error, not an accuracy percentage.
fig, ax = plt.subplots(figsize=(8, 4.1), layout="constrained")
bars = ax.barh(["Family-median baseline", "LightGBM runtime model"], [baseline_mdape, model_mdape], color=["#9baabc", TEAL], height=.5)
ax.bar_label(bars, labels=[f"{baseline_mdape:.2f}%", f"{model_mdape:.2f}%"], padding=6, fontsize=13)
ax.set(xlim=(0, 29), xlabel="Held-out MdAPE (%) - lower is better"); ax.grid(axis="x", alpha=.15)
save(fig, "F07_mdape", "Runtime prediction error against the baseline", "MdAPE = median(|prediction - actual| / actual) x 100, recomputed on the 24 saved test rows. LightGBM: 13.84%; same-training-split family-median baseline: 23.01%. This is an error metric. Subtracting it from 100 does not create a valid model accuracy measure.", ["artifacts/main_v1/runtime_test_predictions.csv", "artifacts/main_v1/runtime_metrics.json"], "Original results")
export_csv("runtime_metrics", [{"metric": "test_mdape_percent", "value": model_mdape, "denominator": "24 rows / 8 groups"}, {"metric": "baseline_mdape_percent", "value": baseline_mdape, "denominator": "same 24 test rows"}, {"metric": "upper_row_coverage", "value": covered / len(pred), "denominator": "24/24 rows"}, {"metric": "upper_group_coverage", "value": metrics["test_group_upper_coverage"], "denominator": "8/8 groups"}])

# F08: upper bounds are one-sided estimates, not an interval around the mean.
ordered = sorted(pred, key=lambda r: (FAMILIES.index(r["family"]), r["config_id"], int(r["repeat_id"])))
fig, ax = plt.subplots(figsize=(11.2, 5.4), layout="constrained")
x = np.arange(24); actual = np.array([float(r["engine_seconds"]) for r in ordered]); point = np.array([float(r["predicted_seconds"]) for r in ordered]); upper = np.array([float(r["upper_seconds"]) for r in ordered])
ax.vlines(x, point, upper, color="#a8c5df", lw=3, label="Point-to-upper span")
ax.scatter(x, point, color=BLUE, marker="o", label="Point prediction", s=25)
ax.scatter(x, upper, color=TEAL, marker="_", s=95, label="Upper estimate")
ax.scatter(x, actual, color=RED, marker="x", label="Actual engine time", s=32)
ax.set_xticks([2.5, 8.5, 14.5, 20.5], [NAMES[f] for f in FAMILIES]); ax.set_ylabel("Engine runtime (seconds)"); ax.set_xlim(-1, 24)
for end in [5.5, 11.5, 17.5]: ax.axvline(end, color="#dce4eb", lw=1)
ax.legend(ncols=2, loc="upper left", fontsize=9); ax.grid(axis="y", alpha=.15)
save(fig, "F08_upper_coverage", "What the calibrated upper estimate covered", "The frozen one-sided upper estimate is point prediction x exp(0.523642), approximately 1.688 times the point prediction. All 24 saved test runtimes were below their bounds (8/8 groups). The nominal calibration target is 90%; 100% observed coverage on this small split is not a population or selected-job success guarantee.", ["artifacts/main_v1/runtime_test_predictions.csv", "artifacts/main_v1/runtime_metrics.json"], "Original results")
export_csv("heldout_predictions", ordered)

# F09: historical older objective, carefully distinguished from current balanced.
values = [policy[k] for k in ["mean_policy_median_cost", "mean_default_median_cost", "mean_conservative_median_cost", "mean_random_expected_median_cost"]]
fig, ax = plt.subplots(figsize=(9.5, 4.5), layout="constrained")
bars = ax.barh(["Historical policy", "Declared reference", "Conservative", "Uniform random"], values, color=[TEAL, BLUE, "#9baabc", GOLD])
ax.bar_label(bars, fmt="%.3f", padding=5); ax.invert_yaxis(); ax.set_xlim(0, max(values) * 1.2)
ax.set_xlabel("Mean median normalized resource cost (historical objective)")
save(fig, "F09_historical_cost", "Historical same-table policy comparison", "The older recommend-model policy has 34.1% lower normalized cost than w1_t1_2g in a descriptive reuse of the original table. Means are over four workload profiles; each selected cell uses three repeats. This is not independent savings, not cloud currency, and not a performance estimate for the newer balanced advise objective.", ["reports/policy_metrics.json", "reports/policy_comparison.csv"], "Original results")

# F10: actual current advisor candidate output, not historical old-policy output.
candidates = advisor["candidates"]
fig, ax = plt.subplots(figsize=(11.2, 5.5), layout="constrained")
y = np.arange(len(candidates))
for i, c in enumerate(candidates):
    color = TEAL if c["eligible"] else RED
    ax.plot([c["predicted_runtime_s"], c["runtime_upper_s"]], [i, i], color=color, lw=2)
    ax.scatter(c["predicted_runtime_s"], i, color=color, s=35)
    ax.scatter(c["runtime_upper_s"], i, color=color, marker="|", s=120)
ax.axvline(advisor["effective_deadline_seconds"], color=GOLD, linestyle="--", label="Engine deadline: 13.1 s")
labels = [c["config_id"] + ("  [selected]" if c["config_id"] == advisor["decision"].get("config_id") else "") for c in candidates]
ax.set_yticks(y, labels); ax.invert_yaxis(); ax.set_xlim(left=0); ax.set_xlabel("Predicted engine seconds: dot = point, end tick = upper")
ax.legend(loc="lower right"); ax.grid(axis="x", alpha=.15)
save(fig, "F10_advisor_candidates", "Worked example: current balanced advisor", 'Actual inference-only CLI output for sort_merge. All eight configurations met the 13.1-second deadline using their upper runtime estimates and passed the resource checks. The advisor selected w2_t2_1g because it had the lowest balanced score. No job was executed for this capture.', ["advisor_capture/sort_balanced.json", "docs/CONFIG_SELECTION.md"], "Implementation")
export_csv("advisor_candidates", [{k: c.get(k) for k in ["config_id", "n_workers", "threads_per_worker", "total_memory_gb", "predicted_runtime_s", "runtime_upper_s", "score", "eligible"]} for c in candidates])

# F11: causal-factor design is a cartoon, not measured category frequencies.
fig, axes = plt.subplots(1, 4, figsize=(11.2, 3.8), layout="constrained")
patterns = [("Balanced", [1, 1, 1, 1], False), ("Key skew only", [1, 1, 1, 1], True), ("Partition imbalance only", [3.1, .3, .3, .3], False), ("Both factors", [3.1, .3, .3, .3], True)]
for ax, (title, heights, skew) in zip(axes, patterns):
    ax.bar(range(4), heights, color=GOLD if skew else BLUE)
    ax.set(xticks=range(4), xticklabels=["P1", "P2", "P3", "P4"], ylim=(0, 3.5), title=title)
    ax.set_yticks([]); ax.set_xlabel("Dominant keys" if skew else "Even key mix")
axes[0].set_ylabel("Illustrative partition size")
save(fig, "F11_pressure_design", "Why separate key skew from partition imbalance?", "Schematic, not measured partition sizes: key skew means keys occur unevenly; partition imbalance means some input partitions hold more data than others. Stage A crossed these two factors for two workload families, producing eight generated instances. The cartoon has four partitions for readability and does not assert the actual partition count.", ["reports/research_stage_a_windows_v1/plan.json (research branch)"], "Research development")

# F12: keep successful restarts distinct from failed jobs.
instances = sorted({r["instance_id"] for r in stage_a["aggregates"]})
short_names = [i.replace("-2000000-", " / ").replace("-s911", "").replace("partition_imbalance_only", "partition imbalance").replace("key_skew_only", "key skew") for i in instances]
cells = np.zeros((8, 2)); labels = []
for i, instance in enumerate(instances):
    rowlabels = []
    for j, cap in enumerate(["w2_t1_1g", "w2_t1_2g"]):
        a = next(a for a in stage_a["aggregates"] if a["instance_id"] == instance and a["target_config_id"] == cap)
        success = a["statuses"].get("success", 0); errors = a["statuses"].get("execution_error", 0)
        cells[i, j] = success; rowlabels.append(f"{success} success / {errors} error")
    labels.append(rowlabels)
fig, ax = plt.subplots(figsize=(11.2, 5.6), layout="constrained")
ax.imshow(cells, cmap="RdYlGn", vmin=0, vmax=3, aspect="auto", alpha=.65)
for i in range(8):
    for j in range(2): ax.text(j, i, labels[i][j], ha="center", va="center", color=INK, weight="bold")
ax.set_yticks(range(8), short_names); ax.set_xticks([0, 1], ["2 workers x 1 thread; 1 GB each", "2 workers x 1 thread; 2 GB each"])
save(fig, "F12_stage_a", "Stage A: full-job outcomes under memory pressure", "Existing Stage A development records: 48 full attempts, 41 successes and seven execution errors. Every grid cell has three repetitions; seven errors have nanny memory-termination evidence. A successful job can also contain worker restart/pressure events, so success does not mean absence of pressure. These are eight instances from one generation seed, not independent reliability estimates.", ["reports/research_stage_a_windows_v1/summary.json (research branch)"], "Research development")
export_csv("stage_a_outcomes", [{"instance_id": a["instance_id"], "config_id": a["target_config_id"], "success": a["statuses"].get("success", 0), "execution_error": a["statuses"].get("execution_error", 0), "observed": a["observed"]} for a in stage_a["aggregates"]])

# F13: quiet probes can miss pressure in full inputs; no rate interpretation.
fig, ax = plt.subplots(figsize=(11.2, 5.6), layout="constrained")
bcols = [(c, f) for c in ["w2_t1_1g", "w2_t1_2g"] for f in [.125, .25]]
bmatrix = np.zeros((8, 4)); brows = []
for i, instance in enumerate(instances):
    for j, (cap, fraction) in enumerate(bcols):
        g = next(g for g in stage_b["fidelity_groups"] if g["instance_id"] == instance and g["target_config_id"] == cap and g["fraction"] == fraction)
        assert g["comparison_available"]
        mismatch = bool(g["false_reassurance_candidate"]); bmatrix[i, j] = int(mismatch)
        brows.append({"instance_id": instance, "target_config_id": cap, "fraction": fraction, "probe_signals": json.dumps(g["probe"]["signals"]), "full_signals": json.dumps(g["full"]["signals"]), "pressure_discrepancy": mismatch})
ax.imshow(bmatrix, cmap=matplotlib.colors.ListedColormap(["#d9eee9", "#f2c6c9"]), vmin=0, vmax=1, aspect="auto")
for i in range(8):
    for j in range(4): ax.text(j, i, "MISSED pressure" if bmatrix[i, j] else "No discrepancy", ha="center", va="center", fontsize=9)
ax.set_yticks(range(8), short_names); ax.set_xticks(range(4), [f"{c[-2:]} target\n{f:g} sample" for c, f in bcols])
save(fig, "F13_stage_b_fidelity", "Stage B: sample quietness is not full-job safety", "All 96 Stage B probes were quiet successes. Eight of 32 paired comparison groups had full-input pressure without a corresponding probe warning. Those eight cells represent four low-cap instance cases observed at two fractions, not eight independent workloads or a calibrated 25% false-negative rate. Sample effective caps and full-target caps are distinct in the source plan.", ["reports/research_stage_b_windows_v1/summary.json (research branch)"], "Research development")
assert int(bmatrix.sum()) == stage_b["comparison_counts"]["false_reassurance_candidate_groups"] == 8
export_csv("stage_b_pressure_comparisons", brows)

# F14: constructed request totals; metadata overhead remains unmeasured.
pkeys = ["fixed_2gb", "dense_bytes_metadata", "always_one_probe_counterfactual", "ambiguous_only_counterfactual", "guarded_default_admission_disabled"]
plabels = ["Fixed 2 GB", "Size-aware metadata", "Always one probe (counterfactual)", "Ambiguous-only probe (counterfactual)", "Guarded default (probe disabled)"]
wallkey = "median_per_instance_constructed_all_attempt_wall_seconds"
pvalues = [feasible["policies"][k][wallkey] for k in pkeys]
fig, ax = plt.subplots(figsize=(11.2, 4.5), layout="constrained")
bars = ax.barh(plabels, pvalues, color=["#9baabc", TEAL, RED, GOLD, BLUE]); ax.bar_label(bars, fmt="%.2f s", padding=5)
ax.invert_yaxis(); ax.set_xlim(0, max(pvalues) * 1.2); ax.set_xlabel("Median constructed per-instance request wall time (seconds)")
save(fig, "F14_probe_cost", "One-probe replay: same historical choices, added cost", "Development counterfactual replay over eight instances: stronger metadata and one-probe rules select the same historical configurations, with 24/24 selected historical full outcomes successful. Metadata-associated request total: 4.79 s; always one probe: 10.37 s; ambiguous-only: 7.38 s. These are constructed totals from different-session historical references, not measured online latency. Metadata/controller overhead is unmeasured; 4.79 s is not metadata-read time. No probe admission was enabled.", ["reports/one_probe_feasibility_20261116/analysis.json (research branch)"], "Research development")
export_csv("one_probe_cost_accounting", [{"policy": k, "median_constructed_request_wall_seconds": feasible["policies"][k][wallkey], "median_profile_wall_seconds": feasible["policies"][k]["median_per_instance_profile_wall_seconds"], "historical_selected_success": feasible["policies"][k]["unique_selected_historical_full_statuses"].get("success", 0), "instances_paying_probe": feasible["policies"][k]["instances_paying_one_probe"]} for k in feasible["policies"]])

# F15: paired evidence from individual lifetimes; never sum asynchronous peaks.
termination_rows = []
for w in workers:
    events = [e for e in w.get("worker_evidence", []) if e["kind"] == "nanny_memory_restart" and e.get("rss_bytes") is not None]
    if not events:
        continue
    assert len(events) == 1 and w["peak_rss_bytes"] is not None and w["effective_memory_limit_bytes"] is not None
    cap = w["effective_memory_limit_bytes"]
    termination_rows.append({"worker_lifetime_id": w["worker_lifetime_id"], "run_id": w["run_id"], "run_status": w["run_status"], "cap_bytes": cap, "saved_peak_rss_bytes": w["peak_rss_bytes"], "event_rss_bytes": events[0]["rss_bytes"], "saved_peak_over_cap": w["peak_rss_bytes"] / cap, "event_rss_over_cap": events[0]["rss_bytes"] / cap, "termination_threshold_ratio": w["memory_settings"]["terminate"]})
assert len(termination_rows) == 37
assert sum(r["saved_peak_over_cap"] < r["termination_threshold_ratio"] for r in termination_rows) == 33
assert sum(r["event_rss_bytes"] > r["saved_peak_rss_bytes"] for r in termination_rows) == 36
termination_rows.sort(key=lambda r: r["saved_peak_over_cap"])
export_csv("terminated_worker_memory", termination_rows)
fig, ax = plt.subplots(figsize=(11.2, 5.1), layout="constrained")
x = np.arange(1, 38); low = np.array([r["saved_peak_over_cap"] for r in termination_rows]); event = np.array([r["event_rss_over_cap"] for r in termination_rows])
ax.vlines(x, low, event, color="#bdcbd8", lw=1.4)
ax.scatter(x, low, color=BLUE, s=25, label="Retained sampled RSS peak")
ax.scatter(x, event, color=RED, marker="x", s=30, label="Nanny-event RSS")
ax.axhline(.95, color=GOLD, linestyle="--", label="Recorded termination threshold: 0.95 x cap")
ax.set(xlabel="Terminated worker lifetime (sorted by retained peak; 37 lifetimes)", ylabel="RSS / effective worker cap", ylim=(.58, 1.2)); ax.legend(loc="upper left", fontsize=9); ax.grid(axis="y", alpha=.15)
save(fig, "F15_worker_memory", "Why sampled peaks are not exact memory-demand labels", "Paired observations for 37 terminated worker lifetimes: 33 retained sampled peaks were below the recorded termination threshold, while event RSS exceeded the retained peak in 36 cases. Sampling and persistence can miss brief peaks before worker death. These are worker lifetimes, not 37 failed jobs; event RSS is a separate observation, not a replacement exact peak or synchronized cluster total. Missing worker values elsewhere remain missing.", ["reports/worker_memory_stage_a_b_v1/workers.json (research branch)", "reports/worker_memory_review_20261116/analysis.json (research branch)"], "Research development")

# F16: show the actual gate, not an aspirational deployed controller.
fig, ax = plt.subplots(figsize=(11.2, 4.8)); ax.axis("off"); ax.set(xlim=(0, 1), ylim=(0, 1))
box(ax, (.02, .56), .25, .24, "Known metadata\n+ supported request", BLUE)
box(ax, (.37, .56), .25, .24, "Default diagnostic policy\nMetadata-based choice", TEAL)
box(ax, (.72, .56), .25, .24, "Select / abstain\nNo new execution", TEAL)
arrow(ax, (.27, .68), (.37, .68)); arrow(ax, (.62, .68), (.72, .68))
box(ax, (.20, .08), .60, .25, "PROBE ADMISSION CLOSED\nNo incremental-information or single-request cost benefit shown\nOne-observation classification is counterfactual diagnostic code", RED)
ax.text(.5, .95, "Separate research prototype: no automatic pilot or Stage C", ha="center", fontsize=14, weight="bold")
save(fig, "F16_closed_gate", "The research gate stays closed", "Conceptual flow of the guarded research prototype. The checked-in default uses no probe; the one-observation path has software checks but remains a diagnostic counterfactual. A new physical pilot needs a revised hypothesis, fair baselines, plausible information/economic benefit, and explicit review. This diagram is not the main advisor architecture or an enabled execution controller.", ["reports/one_probe_feasibility_20261116/analysis.json (research branch)", "reports/one_probe_windows_checks_v1/verification.json (research branch)"], "Research development")

# F17: software counts with distinct scope and explicit zero fresh executions.
fig, ax = plt.subplots(figsize=(11.2, 3.6)); ax.axis("off"); ax.set(xlim=(0, 1), ylim=(0, 1))
for x, value, label, color in [(.02, "143", "Main-advisor tests passed\n0 failed / 0 errors / 0 skipped", TEAL), (.355, "38", "Research targeted tests passed\n8 defaults / 24 counterfactual checks", BLUE), (.69, "0", "Fresh main-study cells executed\nPreparation still awaits review", GOLD)]:
    box(ax, (x, .18), .29, .66, value + "\n\n" + label, color)
save(fig, "F17_verification", "Verified software is a checkpoint, not a fresh experiment", "The original-advisor full Windows suite passed 143 tests in 36.89 s at d6f906a. The separately verified research module passed 38 targeted synthetic tests and checked 8 default decisions, 24 single-observation counterfactuals and 37 termination records. These scopes differ: do not add them as a single suite or count tests as benchmarks. The new main study has zero executed cells.", ["reports/main_validation_windows_checks_v1/verification.json", "reports/one_probe_windows_checks_v1/verification.json (research branch)"], "Verification")

# F18: earlier development screen, with its restricted timing denominator.
method_keys = ["uniform", "uniform_memory", "partition_tail"]
method_names = ["Uniform sample", "Memory-mapped uniform", "Partition-tail sample"]
regrets = [screen["methods"][k]["engine_regret_percent"]["median"] for k in method_keys]
assert all(screen["methods"][k]["engine_regret_percent"]["n"] == 10 for k in method_keys)
fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
bars = ax.barh(method_names, regrets, color=[BLUE, TEAL, GOLD])
ax.bar_label(bars, labels=[f"{v:.2f}%" for v in regrets], padding=5)
ax.invert_yaxis(); ax.set_xlim(0, max(regrets) * 1.3)
ax.set_xlabel("Median selected-full engine regret (%) - lower is better")
save(fig, "F18_screen_regret", "Earlier screen: probe ranking was not a free improvement",
     "Post-hoc development replay on ten complete eligible instances out of twelve generated recipes: median selected-full engine regret was 3.87% for uniform, 0.11% for memory-mapped uniform and 8.17% for partition-tail. Regret compares the selected full-engine outcome with the retrospective full-engine reference; it is not prediction accuracy or complete-request savings. The full screen retains 768 attempts (759 success, one timeout, eight execution errors), one generation seed and two runtime repeats. Timing exclusions do not remove failures from the study record.",
     ["reports/research_screen_review_20261114/analysis.json (research branch)"], "Research development")
export_csv("screen_engine_regret", [{"method": k, **screen["methods"][k]["engine_regret_percent"], "scope": "10 complete eligible instances; post-hoc engine-only replay"} for k in method_keys])

# Tables for writing and audit, without manufacturing training histories.
export_csv("software_verification", [{"suite": "Original advisor full suite", **receipt["tests"], "scope": "software incl tiny Dask fixtures", "tested_commit": receipt["git_revision"]}, {"suite": "Separate research targeted checks", "collected": one_probe_checks["tests_passed"], "passed": one_probe_checks["tests_passed"], "failed": 0, "errors": 0, "skipped": 0, "scope": "targeted synthetic and compact-evidence checks; not fresh experiments", "tested_commit": "see research verification receipt"}])
facts = {"original_jobs": len(runs), "original_successes": 96, "test_rows": len(pred), "test_groups": 8,
         "test_mdape_percent": model_mdape, "baseline_mdape_percent": baseline_mdape,
         "upper_covered_rows": covered, "stage_a_attempts": stage_a["recorded_cells"],
         "stage_a_statuses": stage_a["statuses"], "stage_b_attempts": stage_b["recorded_cells"],
         "stage_b_pressure_discrepancy_groups": int(bmatrix.sum()),
         "terminated_worker_lifetimes": len(termination_rows), "saved_peaks_below_threshold": 33,
         "event_rss_exceeds_saved_peak": 36, "probe_admission_enabled": False,
         "main_software_tests": receipt["tests"], "fresh_main_study_cells": 0,
         "training_accuracy_available": False, "training_curve_available": False,
         "screen_role": screen["role"], "research_memory_export_lifetimes": len(workers)}
(HERE / "verified_facts.json").write_text(json.dumps(facts, indent=2) + "\n")
(HERE / "figure_register.json").write_text(json.dumps(figures, indent=2) + "\n")
(HERE / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
source_check()
print(json.dumps({"figures": len(figures), "csv_tables": len(list(TABLE.glob('*.csv'))), "facts_checked": True,
                  "original_verified_sources_unchanged": True, "output": str(HERE)}, indent=2))
