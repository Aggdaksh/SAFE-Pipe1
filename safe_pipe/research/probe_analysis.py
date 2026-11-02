"""Descriptive proxy-ranking audit, deliberately separate from policy evaluation."""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
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
    return {
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


def markdown_report(summary: dict[str, Any]) -> str:
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
