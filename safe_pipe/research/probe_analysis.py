"""Descriptive proxy-ranking audit, deliberately separate from policy evaluation."""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import math
from statistics import median
from typing import Any


def _order(a: list[float], b: list[float], tolerance: float) -> int:
    """Nonoverlapping observed ranges plus a practical gap; NOT a significance test."""
    ma, mb = median(a), median(b)
    if abs(ma - mb) / min(ma, mb) <= tolerance:
        return 0
    if max(a) < min(b):
        return -1
    if max(b) < min(a):
        return 1
    return 0


def summarize(plan: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    if plan.get("preset") == "windows-stage-b":
        from safe_pipe.research.probe_fidelity import summarize_stage_b
        return summarize_stage_b(plan, records)
    expected = {c["cell_id"]: c for c in plan["cells"]}
    seen: set[str] = set()
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        cell_id = row["cell_id"]
        if cell_id not in expected or cell_id in seen:
            raise ValueError(f"unknown or duplicated cell: {cell_id}")
        cell = expected[cell_id]
        for key in ("instance_id", "method", "target_config_id", "repeat_id"):
            if row[key] != cell[key]:
                raise ValueError(f"cell identity mismatch: {cell_id}/{key}")
        seen.add(cell_id)
        groups[(row["instance_id"], row["method"], row["target_config_id"])].append(row)

    configs = [c["config_id"] for c in plan["configs"]]
    repeats = plan["repeats"]
    tolerance = plan["ranking_tolerance"]
    aggregates = []
    timings: dict[tuple[str, str, str], list[float]] = {}
    for key, rows in sorted(groups.items()):
        values = [r.get("timings", {}).get("execution_seconds") for r in rows if r["status"] == "success"]
        valid = [float(v) for v in values if isinstance(v, (int, float)) and v > 0]
        complete = len(rows) == repeats and len(valid) == repeats
        if complete:
            timings[key] = valid
        aggregates.append({"instance_id": key[0], "method": key[1], "target_config_id": key[2],
                           "observed": len(rows), "expected": repeats,
                           "statuses": dict(Counter(r["status"] for r in rows)),
                           "complete_success": complete,
                           "engine_seconds": valid,
                           "median_engine_seconds": median(valid) if valid else None})

    comparisons = []
    for instance_id in sorted(plan["datasets"]):
        for method in plan["methods"]:
            if method == "full":
                continue
            full = {c: timings.get((instance_id, "full", c)) for c in configs}
            probe = {c: timings.get((instance_id, method, c)) for c in configs}
            result: dict[str, Any] = {"instance_id": instance_id, "method": method}
            if not all(full.values()) or not all(probe.values()):
                result.update(evaluable=False, reason="requires all declared candidates/repeats to succeed; failures retained separately")
                comparisons.append(result)
                continue
            states: Counter[str] = Counter()
            pairs = []
            for a, b in combinations(configs, 2):
                reference_order = _order(full[a], full[b], tolerance)
                probe_order = _order(probe[a], probe[b], tolerance)
                state = ("reference_unresolved" if not reference_order else
                         "probe_unresolved" if not probe_order else
                         "aligned" if reference_order == probe_order else "inverted")
                states[state] += 1
                pairs.append({"a": a, "b": b, "state": state})
            selected = min(configs, key=lambda c: (median(probe[c]), c))
            best = min(configs, key=lambda c: (median(full[c]), c))
            resolved = states["aligned"] + states["inverted"]
            result.update(evaluable=True, pairs=pairs, pair_counts=dict(states),
                          inversion_fraction_among_resolved=states["inverted"] / resolved if resolved else None,
                          proxy_selected_config=selected, hindsight_median_best_config=best,
                          selected_full_engine_regret=median(full[selected]) / median(full[best]) - 1,
                          selection_distinguishable_from_best=bool(_order(full[selected], full[best], tolerance)))
            comparisons.append(result)

    telemetry = []
    for r in records:
        t = r.get("telemetry") or {}
        telemetry.append({"cell_id": r["cell_id"], "instance_id": r["instance_id"], "method": r["method"],
                          "target_config_id": r["target_config_id"], "status": r["status"], **t})
    summary = {
        "schema_version": "probe-ranking-report-v1", "role": plan["role"],
        "planned_cells": len(expected), "recorded_cells": len(records),
        "missing_cells": sorted(set(expected) - seen),
        "statuses": dict(Counter(r["status"] for r in records)),
        "ranking_tolerance": tolerance,
        "method_notes": [
            "Development proxy-ranking screen, not an adaptive-policy evaluation or a novelty result.",
            "Ranks use execution time after cluster setup; all lifecycle timing remains in raw records.",
            "A decisive pair requires > tolerance median gap and nonoverlapping observed repeat ranges; not a statistical confidence interval.",
            "All candidates/repeats must succeed for a numerical ranking comparison; failures/incomplete groups are not silently dropped.",
            "Full and probe outcomes share instances: this is paired descriptive analysis, not held-out prediction accuracy.",
            "No end-to-end savings or deadline guarantee is computed from this matrix.",
            "Large input partitions are a heuristic for expensive work, not measured post-shuffle working sets.",
        ],
        "aggregates": aggregates, "comparisons": comparisons, "telemetry_by_cell": telemetry,
    }
    if plan.get("preset") == "windows-stage-a":
        summary["mechanism"] = mechanism_summary(plan, records)
    return summary


def mechanism_summary(plan: dict, records: list[dict]) -> dict:
    """Keep failure, unknown telemetry, missing repeats and confounding visible."""
    cells = []
    inconsistent = []
    for recipe in plan["recipes"]:
        instance_rows = [r for r in records if r["instance_id"] == recipe["instance_id"]]
        results = [r.get("result_value") for r in instance_rows if r["status"] == "success"]
        if results and (any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in results)
                        or any(not math.isclose(v, results[0], rel_tol=1e-9, abs_tol=1e-9) for v in results)):
            inconsistent.append(recipe["instance_id"])
        for config in plan["configs"]:
            rows = [r for r in instance_rows if r["target_config_id"] == config["config_id"]]
            successful = [r for r in rows if r["status"] == "success"]
            spill = [(r.get("telemetry") or {}).get("spilled_disk_peak_bytes_sum") for r in rows]
            cells.append({"instance_id": recipe["instance_id"], "config_id": config["config_id"],
                          "family": recipe["family"], "hot_fraction": recipe["hot_fraction"],
                          "partition_imbalance": recipe["partition_imbalance"],
                          "observed": len(rows), "expected": plan["repeats"],
                          "statuses": dict(Counter(r["status"] for r in rows)),
                          "condition_flagged": sum(bool((r.get("conditions") or {}).get("flags")) for r in rows),
                          "spill_positive": sum(v is not None and v > 0 for v in spill),
                          "spill_unknown": sum(v is None for v in spill),
                          "nanny_memory_positive": sum(((r.get("diagnostics") or {}).get("nanny_memory_termination_count") or 0) > 0 for r in rows),
                          "diagnosis_unknown": sum("unknown" in (r.get("diagnostics") or {}).get("failure_category", "unknown") for r in rows),
                          "diagnosis_unavailable": sum(not r.get("diagnostics") or bool(r["diagnostics"].get("summary_error")) for r in rows),
                          "successful_engine_seconds": [r["timings"].get("execution_seconds") for r in successful],
                          "attempt_lifecycle_seconds": [r.get("timings", {}).get("total_seconds") for r in rows]})
    return {"groups": cells, "inconsistent_successful_results": inconsistent,
            "gate": "MANUAL REVIEW REQUIRED; no automatic Stage B or model training",
            "limits": "One generation seed and three runtime repeats. This isolates declared factors; "
                      "it is not an independent final study or proof of general failure probability. "
                      "Result agreement across configs is a consistency check, not a large-input correctness oracle."}


def markdown_report(summary: dict[str, Any]) -> str:
    if summary.get("schema_version") == "stage-b-fidelity-report-v1":
        from safe_pipe.research.probe_fidelity import markdown_stage_b
        return markdown_stage_b(summary)
    if "mechanism" in summary:
        mechanism = summary["mechanism"]
        lines = ["# Stage A mechanism diagnosis", "",
                 f"Recorded {summary['recorded_cells']} / {summary['planned_cells']} planned attempts.", "",
                 "All statuses and condition flags are retained. No probe ranking or controller benefit is inferred.", "",
                 "| Instance | Config | Observed / planned | Statuses | Spill positive / unknown | Nanny memory positive | Condition flags |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
        for group in mechanism["groups"]:
            lines.append(f"| {group['instance_id']} | {group['config_id']} | {group['observed']} / {group['expected']} | "
                         f"{group['statuses']} | {group['spill_positive']} / {group['spill_unknown']} | "
                         f"{group['nanny_memory_positive']} | {group['condition_flagged']} |")
        lines += ["", f"Inconsistent successful scalar results: {mechanism['inconsistent_successful_results']}", "",
                  mechanism["gate"], "", mechanism["limits"], ""]
        return "\n".join(lines)
    lines = ["# Research probe development screen", "",
             f"Recorded {summary['recorded_cells']} / {summary['planned_cells']} planned cells.", "",
             f"Statuses: `{summary['statuses']}`.", "",
             "**This report does not establish novelty, spill reduction, or online policy improvement.**", "",
             "| Instance | Proxy | Aligned / inverted / unresolved pairs | Proxy choice | Full-engine regret |",
             "| --- | --- | --- | --- | --- |"]
    for c in summary["comparisons"]:
        if not c["evaluable"]:
            lines.append(f"| {c['instance_id']} | {c['method']} | Incomplete or failed | — | — |")
            continue
        counts = c["pair_counts"]
        unresolved = counts.get("reference_unresolved", 0) + counts.get("probe_unresolved", 0)
        lines.append(f"| {c['instance_id']} | {c['method']} | {counts.get('aligned', 0)} / {counts.get('inverted', 0)} / {unresolved} | {c['proxy_selected_config']} | {100*c['selected_full_engine_regret']:.2f}% |")
    lines += ["", "## Interpretation limits", ""]
    lines += [f"- {note}" for note in summary["method_notes"]]
    lines += ["", "Inspect worker telemetry, graph signatures, actual sample row/byte budgets and failures before interpreting any ranking change.", ""]
    return "\n".join(lines)
