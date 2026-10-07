from __future__ import annotations

"""R10 evidence additions for the bounded-release calculus.

This script adds only deterministic checks grounded in already archived project
inputs: the global-vs-group scale intersection, predicate/action blocking
matrix, cross-table effective-modulus transfer, and two argument figures.
These are method controls, not independent physical validation.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from brr.actions import reduce_action  # noqa: E402
from brr.schema import (  # noqa: E402
    ActionLevel,
    BoundedRelationRun,
    Evidence,
    EvidenceClass,
    Object,
    Predicate,
    PredicateType,
    Provenance,
    Relation,
    Response,
    State,
)

OUT = ROOT / "outputs"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

HALF_UNIT = 0.005
ANGLE_RELATION = lambda x: 0.292 - 0.339 * x**2 + 1.060 * x


def dummy_run(overrides: dict[PredicateType, bool | None] | None = None) -> BoundedRelationRun:
    overrides = overrides or {}
    predicates = []
    specs = [
        (PredicateType.MECHANICS_POSITIVITY, "mechanics.positivity"),
        (PredicateType.MECHANICS_FINITENESS, "mechanics.finiteness"),
        (PredicateType.MECHANICS_MONOTONICITY, "mechanics.monotonicity"),
        (PredicateType.EVIDENCE_INTERVAL_FEASIBILITY, "evidence.interval_feasibility"),
        (PredicateType.EVIDENCE_COVERAGE, "evidence.coverage"),
        (PredicateType.PROVENANCE_SOURCE_VERIFIED, "provenance.source_verified"),
        (PredicateType.PROVENANCE_SELECTOR_VERIFIED, "provenance.selector_verified"),
    ]
    for kind, pid in specs:
        predicates.append(
            Predicate(
                predicate_id=pid,
                predicate_type=kind,
                expression="predeclared control predicate",
                declared_by="R10 method control",
                result=overrides.get(kind, True),
            )
        )
    return BoundedRelationRun(
        run_id="r10_control",
        object=Object("synthetic-control", "direct-response", {}),
        state=State("x", (1.1, 1.5), [1.1, 1.2, 1.3, 1.4, 1.5]),
        response=Response("response", "source units", True),
        relation=Relation("q", "quadratic", "declared finite class", (1.1, 1.5)),
        predicates=predicates,
        evidence=[Evidence("control", EvidenceClass.METHOD, 20, HALF_UNIT, ["local-control"])],
        provenance=[Provenance("local-control", "outputs/r02_failure_injection_results.csv")],
    )


def predicate_action_matrix() -> pd.DataFrame:
    rows = [{"scenario": "clean positive control", "changed_predicate": "none", "result": reduce_action(dummy_run()).level.name, "expected_order": 2}]
    cases = [
        (PredicateType.MECHANICS_POSITIVITY, "mechanics.positivity = false", 0),
        (PredicateType.MECHANICS_FINITENESS, "mechanics.finiteness = false", 0),
        (PredicateType.MECHANICS_MONOTONICITY, "mechanics.monotonicity = false", 1),
        (PredicateType.EVIDENCE_INTERVAL_FEASIBILITY, "evidence.interval_feasibility = false", 1),
        (PredicateType.EVIDENCE_COVERAGE, "evidence.coverage = false", 1),
        (PredicateType.PROVENANCE_SOURCE_VERIFIED, "provenance.source_verified = false", 0),
        (PredicateType.PROVENANCE_SELECTOR_VERIFIED, "provenance.selector_verified = open", 1),
    ]
    for kind, label, expected in cases:
        value = None if kind == PredicateType.PROVENANCE_SELECTOR_VERIFIED else False
        action = reduce_action(dummy_run({kind: value})).level
        rows.append({"scenario": "single-gate perturbation", "changed_predicate": label, "result": action.name, "expected_order": expected})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r10_predicate_action_matrix.csv", index=False)
    return df


def global_scale_check() -> dict:
    data = pd.read_csv(ROOT / "data" / "source_table_transcription.csv")
    data["q"] = ANGLE_RELATION(data["a_over_b"].to_numpy(float))
    data["lo"] = (data["reported_formula_stress_mpa"] - HALF_UNIT) / data["q"]
    data["hi"] = (data["reported_formula_stress_mpa"] + HALF_UNIT) / data["q"]
    group_cols = ["table", "a_over_t"]
    group_rows = []
    for key, group in data.groupby(group_cols, sort=True):
        group_rows.append({
            "group": f"{key[0]} @ a/t={key[1]:g}",
            "lower": float(group["lo"].max()),
            "upper": float(group["hi"].min()),
            "width": float(group["hi"].min() - group["lo"].max()),
            "cells": int(len(group)),
        })
    global_lower = float(data["lo"].max())
    global_upper = float(data["hi"].min())
    result = {
        "displayed_half_unit_mpa": HALF_UNIT,
        "relation": "q(x)=0.292-0.339x^2+1.060x",
        "groups": group_rows,
        "groupwise_intersection_nonempty": bool(all(r["width"] >= 0 for r in group_rows)),
        "global_lower": global_lower,
        "global_upper": global_upper,
        "global_intersection_nonempty": bool(global_lower <= global_upper),
        "interpretation": "A single global scale is infeasible at the displayed half-unit; the groupwise contract is essential.",
    }
    (OUT / "r10_global_scale_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def cross_table_transfer() -> pd.DataFrame:
    chunks = sorted(OUT.glob("r03_zhang_reconstruction_chunk_*.csv"))
    frame = pd.concat([pd.read_csv(p) for p in chunks], ignore_index=True)
    sentinel = frame[(frame["a_over_t"] == 40) & (frame["a_over_b"] == 1.1) & (frame["c_over_a"].isin([0.2, 0.5]))]
    rows = []
    for source, target in [("Table 4", "Table 8"), ("Table 8", "Table 4")]:
        cal = sentinel[sentinel["table"] == source]
        factor = float(np.sum(cal["reconstructed_stress_mpa"] * cal["source_stress_mpa"]) / np.sum(cal["reconstructed_stress_mpa"] ** 2))
        scored = frame[frame["table"] == target].copy()
        scored["transferred_prediction_mpa"] = scored["reconstructed_stress_mpa"] * factor
        err = (scored["transferred_prediction_mpa"] - scored["source_stress_mpa"]) / scored["source_stress_mpa"] * 100.0
        rows.append({
            "calibration_table": source,
            "scored_table": target,
            "sentinel_rows": int(len(cal)),
            "scale_factor_relative_to_E_effective": factor,
            "rmse_relative_pct": float(np.sqrt(np.mean(err**2))),
            "q95_abs_relative_pct": float(np.quantile(np.abs(err), 0.95)),
            "max_abs_relative_pct": float(np.max(np.abs(err))),
            "within_5pct_fraction": float(np.mean(np.abs(err) <= 5.0)),
            "evidence_class": "cross-table transfer within the same published source; not independent validation",
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r10_cross_table_modulus_transfer.csv", index=False)
    return df


def theory_properties(matrix: pd.DataFrame, global_scale: dict, transfer: pd.DataFrame) -> dict:
    order = {"REJECT_NONEXECUTABLE": 0, "RETAIN_BOUNDED_CLAIM": 1, "ALLOW_BOUNDED_QUERY": 2}
    baseline = order[matrix.iloc[0]["result"]]
    blocking_ok = bool(all(order[r] <= baseline for r in matrix["result"]))
    result = {
        "deterministic_action_count": int(matrix["result"].nunique()),
        "single_action_for_each_control": bool(matrix["result"].notna().all()),
        "monotone_blocking_single_gate_controls": blocking_ok,
        "computational_action_maximum": "ALLOW_BOUNDED_QUERY",
        "operational_use_emitted": False,
        "global_scale_infeasible": not global_scale["global_intersection_nonempty"],
        "cross_table_transfer_rows": int(len(transfer)),
        "boundary": "formal reducer properties are implementation-level properties; case transfer is not universal validation",
    }
    (OUT / "r10_theory_properties.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def figure_calculus(matrix: pd.DataFrame, global_scale: dict, transfer: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(12.0, 7.2), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.08, 1.0])
    ax0 = fig.add_subplot(gs[0, :])
    ax0.axis("off")
    # Center the headings over their boxes so the mechanism remains legible at
    # single-column width; the previous left-anchored labels collided.
    ax0.text(0.12, 0.78, r"Typed contract $\Gamma=(\tau,\mathcal{Q},E,P,V)$",
             ha="center", fontsize=11.5, weight="bold")
    ax0.text(0.415, 0.78, "fixed predicate evaluation", ha="center",
             fontsize=11.5, weight="bold")
    ax0.text(0.80, 0.78, "one computational permission", ha="center",
             fontsize=11.5, weight="bold")
    boxes = [(0.01, 0.30, 0.22, 0.32, "object / state / response\ndomain + candidate class\nrounded cells + provenance", "#E8F1FA"),
             (0.29, 0.30, 0.25, 0.32, "mechanics → evidence → provenance\n\nfit is not a release predicate", "#F4EFE3"),
             (0.66, 0.30, 0.28, 0.32, "REJECT  →  RETAIN  →  ALLOW\n\noperational use remains outside\ncomputational closure", "#E7F3E8")]
    for x, y, w, h, label, color in boxes:
        ax0.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#243447", linewidth=1.3))
        ax0.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=11)
    ax0.annotate("", xy=(0.64, 0.46), xytext=(0.55, 0.46), arrowprops={"arrowstyle": "->", "lw": 2})
    ax0.annotate("", xy=(0.27, 0.46), xytext=(0.23, 0.46), arrowprops={"arrowstyle": "->", "lw": 2})
    ax0.text(0.80, 0.14, "OP", color="#A23E48", ha="center", fontsize=10, weight="bold")
    ax0.text(0.5, 0.08, "tested properties: determinism • monotone blocking • finite-class closure • scale non-identification • fitting independence",
             ha="center", fontsize=9.0, color="#243447")

    ax1 = fig.add_subplot(gs[1, 0])
    colors = {"ALLOW_BOUNDED_QUERY": "#2A9D8F", "RETAIN_BOUNDED_CLAIM": "#E9C46A", "REJECT_NONEXECUTABLE": "#E76F51"}
    y = np.arange(len(matrix))
    ax1.barh(y, matrix["expected_order"], color=[colors[v] for v in matrix["result"]], edgecolor="#243447")
    ax1.set_yticks(y, [s.replace("single-gate perturbation", "gate perturbation") for s in matrix["changed_predicate"]], fontsize=8.2)
    ax1.set_xlim(0, 2.35); ax1.set_xticks([0, 1, 2], ["reject", "retain", "allow"])
    ax1.invert_yaxis(); ax1.set_title("A  Gate failure only blocks release", loc="left", weight="bold", fontsize=11)
    ax1.grid(axis="x", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 1])
    labels = [f"{r.calibration_table} → {r.scored_table}" for r in transfer.itertuples()]
    vals = transfer["rmse_relative_pct"].to_numpy()
    bars = ax2.bar(labels, vals, color=["#457B9D", "#A8DADC"], edgecolor="#243447")
    ax2.set_ylabel("relative RMSE (%)")
    ax2.set_title("B  Cross-table transfer remains bounded", loc="left", weight="bold", fontsize=11)
    ax2.grid(axis="y", alpha=0.25)
    for b, v in zip(bars, vals): ax2.text(b.get_x()+b.get_width()/2, v+0.03, f"{v:.3f}", ha="center", fontsize=9)
    ax2.text(0.02, 0.95, "same Zhang source; not independent validation", transform=ax2.transAxes, fontsize=8.5, va="top", color="#555")

    fig.savefig(FIG / "figure12_bounded_release_calculus.pdf", bbox_inches="tight")
    fig.savefig(FIG / "figure12_bounded_release_calculus.svg", bbox_inches="tight")
    fig.savefig(FIG / "figure12_bounded_release_calculus.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    groups = global_scale["groups"]
    yy = np.arange(len(groups))
    for i, row in enumerate(groups):
        ax.plot([row["lower"], row["upper"]], [i, i], lw=6, solid_capstyle="butt", color="#457B9D")
        ax.plot([row["lower"], row["upper"]], [i, i], "|", ms=14, color="#1D3557")
    ax.axvline(global_scale["global_lower"], ls="--", color="#E76F51", lw=1.5, label=f"global lower={global_scale['global_lower']:.2f}")
    ax.axvline(global_scale["global_upper"], ls=":", color="#E76F51", lw=1.5, label=f"global upper={global_scale['global_upper']:.2f}")
    ax.set_yticks(yy, [r["group"] for r in groups], fontsize=9)
    ax.set_xlabel("positive scale interval at displayed half-unit (MPa per q-unit)")
    ax.set_title("Global scale infeasibility is a result, not a disclaimer")
    ax.grid(axis="x", alpha=0.22); ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "figure13_scale_nonidentification.pdf", bbox_inches="tight")
    fig.savefig(FIG / "figure13_scale_nonidentification.svg", bbox_inches="tight")
    fig.savefig(FIG / "figure13_scale_nonidentification.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    matrix = predicate_action_matrix()
    scale = global_scale_check()
    transfer = cross_table_transfer()
    props = theory_properties(matrix, scale, transfer)
    figure_calculus(matrix, scale, transfer)
    print(json.dumps({"theory_properties": props, "global_scale": scale, "transfer": transfer.to_dict(orient="records")}, indent=2))


if __name__ == "__main__":
    main()
