from __future__ import annotations

"""Bounded-release evidence additions for the bounded-release calculus.

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
                declared_by="bounded-release method control",
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
    # Both figures are drawn on a canvas that matches the Elsevier preprint text
    # column (391 pt = 5.43 in) so the LaTeX scale factor is 1.0 and every label
    # prints at its design size. Text is deliberately ASCII-only: an earlier
    # version used arrows and bullets that vanished after a source round-trip.
    fig = plt.figure(figsize=(5.43, 4.7), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25])
    ax0 = fig.add_subplot(gs[0, :])
    ax0.axis("off")
    ax0.text(0.16, 0.92, "typed contract", ha="center", va="top", fontsize=8.4, weight="bold")
    ax0.text(0.50, 0.92, "fixed predicates", ha="center", va="top", fontsize=8.4, weight="bold")
    ax0.text(0.84, 0.92, "one permission", ha="center", va="top", fontsize=8.4, weight="bold")
    boxes = [
        (0.000, 0.34, 0.315, 0.42,
         "object, state, response\ndomain, candidate class\ncells + provenance", "#E8F1FA"),
        (0.350, 0.34, 0.300, 0.42,
         "mechanics, evidence,\nprovenance\n\nfit is not a\nrelease predicate", "#F4EFE3"),
        (0.685, 0.34, 0.315, 0.42,
         "REJECT > RETAIN\n> ALLOW\n\noperational use stays\noutside the closure", "#E7F3E8"),
    ]
    for x, y, w, h, label, color in boxes:
        ax0.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#243447", linewidth=1.0))
        ax0.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=6.8)
    ax0.annotate("", xy=(0.347, 0.55), xytext=(0.317, 0.55), arrowprops={"arrowstyle": "->", "lw": 1.3})
    ax0.annotate("", xy=(0.682, 0.55), xytext=(0.652, 0.55), arrowprops={"arrowstyle": "->", "lw": 1.3})
    ax0.text(0.845, 0.20, "OP", color="#A23E48", ha="center", va="top", fontsize=7.6, weight="bold")
    ax0.text(0.5, 0.02, "tested: determinism, monotone blocking, finite-class closure,\n"
                        "scale non-identification, fitting independence",
             ha="center", va="bottom", fontsize=7.0, color="#243447")

    ax1 = fig.add_subplot(gs[1, 0])
    action_order = {"REJECT_NONEXECUTABLE": 0, "RETAIN_BOUNDED_CLAIM": 1, "ALLOW_BOUNDED_QUERY": 2}
    colors = {"ALLOW_BOUNDED_QUERY": "#2A9D8F", "RETAIN_BOUNDED_CLAIM": "#E9C46A", "REJECT_NONEXECUTABLE": "#E76F51"}
    # Encode the reduced action as a categorical block, not as a bar length. A length
    # encoding made every REJECT row a zero-width bar, so the blocker path -- the
    # point of the panel -- was invisible.
    levels = np.array([action_order[v] for v in matrix["result"]], dtype=float)
    y = np.arange(len(matrix), dtype=float)
    ax1.barh(y, np.full(len(matrix), 0.82), left=levels - 0.41,
             color=[colors[v] for v in matrix["result"]], edgecolor="#243447", height=0.60)
    shorten = {"mechanics.": "mech.", "evidence.": "evid.", "provenance.": "prov."}
    row_labels = []
    for s in matrix["changed_predicate"]:
        if s == "none":
            lab = "no gate failed"
        else:
            lab = s.replace("single-gate perturbation", "gate perturbation")
            lab = lab.replace(" = false", "").replace(" = open", " (open)")
        for key, val in shorten.items():
            lab = lab.replace(key, val)
        row_labels.append(lab)
    ax1.set_yticks(y, row_labels, fontsize=7.4)
    ax1.set_xlim(-0.62, 2.62)
    ax1.set_xticks([0, 1, 2], ["reject", "retain", "allow"])
    ax1.tick_params(axis="x", labelsize=7.4)
    ax1.set_xlabel("reduced action", fontsize=7.4)
    ax1.invert_yaxis()
    ax1.set_title("A  One changed gate, one action", loc="left", weight="bold", fontsize=8.2)
    ax1.grid(axis="x", alpha=0.25)

    ax2 = fig.add_subplot(gs[1, 1])
    labels = [f"{r.calibration_table}\nto {r.scored_table}" for r in transfer.itertuples()]
    vals = transfer["rmse_relative_pct"].to_numpy()
    bars = ax2.bar(labels, vals, color=["#457B9D", "#A8DADC"], edgecolor="#243447")
    ax2.set_ylabel("relative RMSE (%)", fontsize=7.4)
    ax2.tick_params(axis="y", labelsize=7.4)
    ax2.tick_params(axis="x", labelsize=7.0)
    ax2.set_ylim(0.0, float(vals.max()) * 1.42)
    ax2.set_title("B  Cross-table transfer", loc="left", weight="bold", fontsize=8.2)
    ax2.grid(axis="y", alpha=0.25)
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + float(vals.max()) * 0.035,
                 f"{v:.3f}", ha="center", fontsize=7.4)
    ax2.text(0.03, 0.97, "same source;\nnot independent", transform=ax2.transAxes,
             fontsize=7.0, va="top", color="#444")

    fig.savefig(FIG / "figure12_bounded_release_calculus.pdf")
    fig.savefig(FIG / "figure12_bounded_release_calculus.svg")
    fig.savefig(FIG / "figure12_bounded_release_calculus.png", dpi=300)
    plt.close(fig)

    groups = global_scale["groups"]

    def group_label(name: str) -> str:
        table, _, ratio = name.partition(" @ ")
        return f"{table} / {ratio.replace('a/t=', 'a/t ')}"

    fig, (axa, axb) = plt.subplots(1, 2, figsize=(5.43, 3.3), constrained_layout=True,
                                   gridspec_kw={"width_ratios": [1.7, 1.0]})
    yy = np.arange(len(groups))
    lo_g, hi_g = float(global_scale["global_lower"]), float(global_scale["global_upper"])
    # The four intervals are about 0.005 MPa wide on a 190 MPa axis, so a length
    # encoding collapses them to hairlines. Position is therefore drawn on a log
    # axis and the interval extent is drawn separately in panel B.
    axa.axvspan(hi_g, lo_g, color="#F3D2CE", alpha=0.75, zorder=0)
    for i, row in enumerate(groups):
        axa.plot([row["lower"], row["upper"]], [i, i], lw=6, solid_capstyle="butt",
                 color="#457B9D", zorder=3)
        axa.plot([row["lower"]], [i], marker="|", ms=14, mew=1.4, color="#1D3557", zorder=4)
        axa.text(row["upper"] * 1.08, i, f"{row['lower']:.3f} to {row['upper']:.3f}",
                 va="center", ha="left", fontsize=7.0, color="#1D3557")
    axa.axvline(lo_g, ls="--", color="#B23A48", lw=1.4,
                label=f"required lower bound = {lo_g:.2f}")
    axa.axvline(hi_g, ls=":", color="#B23A48", lw=1.4,
                label=f"required upper bound = {hi_g:.2f}")
    axa.set_xscale("log")
    axa.set_xlim(56, 470)
    # Label only chosen decades: the default sub-decade log minor labels collided.
    axa.set_xticks([60, 80, 100, 150, 200, 300, 400])
    axa.set_xticklabels(["60", "80", "100", "150", "200", "300", "400"])
    axa.xaxis.set_minor_formatter(plt.NullFormatter())
    axa.set_yticks(yy, [group_label(r["group"]) for r in groups], fontsize=7.6)
    axa.set_ylim(-0.75, len(groups) - 0.25)
    axa.set_xlabel("positive group scale $A_g$ (MPa per $q$-unit)", fontsize=7.6)
    axa.tick_params(axis="x", labelsize=7.2)
    axa.set_title("A  Groupwise intervals", loc="left", weight="bold", fontsize=8.2)
    axa.grid(axis="x", alpha=0.22, which="both")
    axa.legend(fontsize=7.0, loc="lower right", framealpha=0.95)
    # No in-panel note: the caption already states that the two bounds are inverted and the
    # band empty. The note used to be struck through by the global-upper dotted line.

    widths = [float(r["width"]) for r in groups]
    short = [group_label(r["group"]).replace("Table ", "T").replace(" / a/t ", "\n") for r in groups]
    axb.bar(short, widths, color="#457B9D", edgecolor="#243447")
    for i, w in enumerate(widths):
        axb.text(i, w * 1.05, f"{w:.5f}", ha="center", fontsize=6.8)
    axb.set_ylim(0, max(widths) * 1.32)
    axb.set_ylabel("interval width (MPa per $q$-unit)", fontsize=7.6)
    axb.set_xlabel("Zhang et al. table / $a/t$", fontsize=7.4)
    axb.tick_params(axis="x", labelsize=6.8)
    axb.tick_params(axis="y", labelsize=7.2)
    axb.set_title("B  Widths are positive", loc="left", weight="bold", fontsize=8.2)
    axb.grid(axis="y", alpha=0.25)
    fig.savefig(FIG / "figure13_scale_nonidentification.pdf")
    fig.savefig(FIG / "figure13_scale_nonidentification.svg")
    fig.savefig(FIG / "figure13_scale_nonidentification.png", dpi=300)
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
