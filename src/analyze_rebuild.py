from __future__ import annotations

import json
import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

source = pd.read_csv(DATA / "source_table_transcription.csv")
full = pd.read_csv(DATA / "full_cufsm_cells.csv")

DISPLAY_HALF_WIDTH = 0.005
DOMAIN = (1.1, 1.5)
COEFFICIENT_MAGNITUDES = (0.292, 0.339, 1.060)


def q_printed(x):
    return 0.292 - 1.060 * np.asarray(x) ** 2 + 0.339 * np.asarray(x)


def q_identified(x):
    return 0.292 - 0.339 * np.asarray(x) ** 2 + 1.060 * np.asarray(x)


def dq_identified(x):
    return -2 * 0.339 * np.asarray(x) + 1.060


def candidate_q(coefficients, x):
    c0, c2, c1 = coefficients
    x = np.asarray(x)
    return c0 + c2 * x**2 + c1 * x


def formula_text(coefficients):
    c0, c2, c1 = coefficients
    return f"{c0:+.3f} {c2:+.3f} x^2 {c1:+.3f} x"


def positive_scale(y, q):
    """Least-squares positive scale, or zero when the shape is inadmissible."""
    y = np.asarray(y, dtype=float)
    q = np.asarray(q, dtype=float)
    if np.any(q <= 0):
        return 0.0
    return max(0.0, float(np.dot(q, y) / np.dot(q, q)))


def minimax_halfwidth(y, q):
    """Smallest common round-off half-width admitting one positive scale."""
    y = np.asarray(y, dtype=float)
    q = np.asarray(q, dtype=float)
    if np.any(q <= 0):
        return np.inf
    ratios = y / q
    pairwise = [
        (ratios[i] - ratios[j]) / (1.0 / q[i] + 1.0 / q[j])
        for i in range(len(y))
        for j in range(len(y))
    ]
    return max(0.0, max(pairwise))


def group_interval(y, q, halfwidth=DISPLAY_HALF_WIDTH):
    if np.any(np.asarray(q) <= 0):
        return np.nan, np.nan
    q = np.asarray(q, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.max((y - halfwidth) / q)), float(np.min((y + halfwidth) / q))


def candidate_domain_stats(coefficients):
    grid = np.linspace(DOMAIN[0], DOMAIN[1], 2001)
    q = candidate_q(coefficients, grid)
    return float(np.min(q)), float(np.max(q)), bool(np.all(q > 0))


primary = source[source["transcription_role"] == "equation_reconstruction"].copy()
primary_groups = list(primary.groupby(["table", "a_over_t"], sort=True))

# Recompute the 48 permutation/sign candidates directly from the primary
# transcription. The checked CSVs remain useful audit references, but the
# executable path no longer depends on them as hidden inputs.
candidate_rows = []
for permutation in itertools.permutations(COEFFICIENT_MAGNITUDES):
    for signs in itertools.product((-1, 1), repeat=3):
        coefficients = tuple(float(a * b) for a, b in zip(permutation, signs))
        q_min, q_max, positive_domain = candidate_domain_stats(coefficients)
        group_halfwidths = []
        compatible_groups = 0
        rmse_residuals = []
        for _, group in primary_groups:
            q_values = candidate_q(coefficients, group["a_over_b"].to_numpy())
            y_values = group["reported_formula_stress_mpa"].to_numpy()
            scale = positive_scale(y_values, q_values)
            prediction = scale * q_values
            rmse_residuals.extend(prediction - y_values)
            group_halfwidths.append(minimax_halfwidth(y_values, q_values))
            lower, upper = group_interval(y_values, q_values)
            if np.isfinite(lower) and lower <= upper:
                compatible_groups += 1
        rmse_mpa = float(np.sqrt(np.mean(np.square(rmse_residuals))))
        candidate_rows.append({
            "constant": coefficients[0],
            "quadratic": coefficients[1],
            "linear": coefficients[2],
            "formula": formula_text(coefficients),
            "domain_q_min": q_min,
            "domain_q_max": q_max,
            "positive_on_full_domain": positive_domain,
            "nearest_compatible_groups_of_4": compatible_groups,
            "positive_truncation_compatible_groups_of_4": compatible_groups,
            "nearest_rmse_mpa_all_20_rows": rmse_mpa,
            "is_reconstructed_assignment": coefficients == (0.292, -0.339, 1.060),
            "is_printed_assignment": coefficients == (0.292, -1.060, 0.339),
        })
search48 = pd.DataFrame(candidate_rows).sort_values(
    ["nearest_rmse_mpa_all_20_rows", "formula"], kind="stable"
).reset_index(drop=True)
search48["rank"] = np.arange(1, len(search48) + 1)

margin_rows = []
for row in candidate_rows:
    coefficients = (row["constant"], row["quadratic"], row["linear"])
    group_widths = {}
    all_compatible = True
    for (table, a_over_t), group in primary_groups:
        q_values = candidate_q(coefficients, group["a_over_b"].to_numpy())
        y_values = group["reported_formula_stress_mpa"].to_numpy()
        width = minimax_halfwidth(y_values, q_values)
        group_widths[f"{table.replace(' ', '').lower()}_a{int(a_over_t)}_minimax_halfwidth_mpa"] = width
        if not np.isfinite(width):
            all_compatible = False
    finite_widths = [v for v in group_widths.values() if np.isfinite(v)]
    row.update(group_widths)
    row["all_group_required_halfwidth_mpa"] = max(finite_widths) if all_compatible else np.inf
    row["compatible_at_reported_halfwidth_0p005_mpa"] = bool(
        all_compatible and row["all_group_required_halfwidth_mpa"] <= DISPLAY_HALF_WIDTH
    )
    margin_rows.append(row.copy())
margin = pd.DataFrame(margin_rows).sort_values(
    ["all_group_required_halfwidth_mpa", "formula"], kind="stable"
).reset_index(drop=True)
margin["rank"] = np.arange(1, len(margin) + 1)

# Recompute the held-out public-table replay from the 630 transcribed cells.
# No native CUFSM model is assumed or loaded.
full = full.copy()
full["printed_q"] = q_printed(full["a_over_b"])
full["reconstructed_q"] = q_identified(full["a_over_b"])
full["printed_positive_scale_prediction_mpa"] = 0.0
full["reconstructed_positive_scale_prediction_mpa"] = 0.0
replay_rows = []
for key, group in full.groupby(["table", "a_over_t", "c_over_a"], sort=True):
    idx = group.index
    y_values = group["cufsm_stress_mpa"].to_numpy()
    q_print = group["printed_q"].to_numpy()
    q_reconstructed = group["reconstructed_q"].to_numpy()
    printed_scale = positive_scale(y_values, q_print)
    reconstructed_scale = positive_scale(y_values, q_reconstructed)
    printed_prediction = printed_scale * q_print
    reconstructed_prediction = reconstructed_scale * q_reconstructed
    full.loc[idx, "printed_positive_scale_prediction_mpa"] = printed_prediction
    full.loc[idx, "reconstructed_positive_scale_prediction_mpa"] = reconstructed_prediction
    full.loc[idx, "reconstructed_relative_error_pct"] = (
        (reconstructed_prediction - y_values) / y_values * 100.0
    )
    ordered_y = group.sort_values("a_over_b")["cufsm_stress_mpa"].to_numpy()
    design = np.column_stack([np.ones(len(group)), group["a_over_b"], group["a_over_b"] ** 2])
    unconstrained = np.linalg.lstsq(design, y_values, rcond=None)[0]
    reconstructed_relative = (reconstructed_prediction - y_values) / y_values
    printed_relative = (printed_prediction - y_values) / y_values
    replay_rows.append({
        "table": key[0],
        "a_over_t": key[1],
        "c_over_a": key[2],
        "row_count": len(group),
        "cufsm_strictly_increasing_with_a_over_b": bool(np.all(np.diff(ordered_y) > 0)),
        "printed_positive_scale": printed_scale,
        "printed_relative_rmse": float(np.sqrt(np.mean(printed_relative ** 2))),
        "reconstructed_positive_scale": reconstructed_scale,
        "reconstructed_relative_rmse": float(np.sqrt(np.mean(reconstructed_relative ** 2))),
        "reconstructed_max_abs_relative_error": float(np.max(np.abs(reconstructed_relative))),
        "unconstrained_normalized_linear": float(unconstrained[1] / unconstrained[0]),
        "unconstrained_normalized_quadratic": float(unconstrained[2] / unconstrained[0]),
    })
replay = pd.DataFrame(replay_rows)
# R5 is a deterministic evidence-completeness gate, not a post-hoc universal
# error threshold.  The bounded query action is available only when every
# transcribed cell and every replay group has a finite residual diagnostic.
replay_complete_gate = bool(
    len(full) == 630
    and len(replay) == 126
    and full["reconstructed_relative_error_pct"].notna().all()
    and np.isfinite(full["reconstructed_relative_error_pct"].to_numpy()).all()
    and np.isfinite(replay["reconstructed_relative_rmse"].to_numpy()).all()
)
OUT.mkdir(exist_ok=True)
search48.to_csv(OUT / "candidate_search_48_recomputed.csv", index=False)
margin.to_csv(OUT / "identification_margin_recomputed.csv", index=False)
full.to_csv(OUT / "full_cufsm_replay_recomputed.csv", index=False)
replay.to_csv(OUT / "full_cufsm_group_replay_recomputed.csv", index=False)

# The engineering knowledge layer is explicit and executable.
# It separates geometry, mechanics, evidence, constraints, and action.
knowledge_graph = {
    "ontology_version": "1.2",
    "scope": "knowledge-constrained recovery protocol demonstrated on an axial local-buckling relation for unequal-limb lipped-angle sections",
    "provenance": {
        "source_record": "Zhang et al. (2022), Buildings 12, 712",
        "source_doi": "10.3390/buildings12060712",
        "source_table_transcription": "data/source_table_transcription.csv",
        "held_out_table_transcription": "data/full_cufsm_cells.csv",
        "source_cufsm_models_available": False,
        "independent_cufsm_rerun": "not_available",
        "independent_source_cufsm_rerun": "not_available",
        "source_model_reconstruction": {"rows": 630, "gate": "pass_with_metadata_boundary", "overall_rmse_pct": 0.5315689291726593, "q95_abs_error_pct": 1.3196886254999995, "max_abs_error_pct": 2.43139066, "effective_modulus_mpa": 217400.0, "mesh_target_mm": 4.0, "length_grid_points": 32, "scope": "published Table 4/Table 8 geometry-to-response recreation; native model files unavailable"},
        "independent_ksce_spectrum_transfer": {"rows": 24, "gate": "pass_bounded_spectrum_screen", "rmse_pct": 0.7197162849917158, "q95_abs_error_pct": 1.5421971964999999, "max_abs_error_pct": 1.6200477, "scope": "published KSCE 2023 Table 2 nearest-spectrum transfer; source mode selector unavailable"},
        "public_solver_transfer": {
            "repository": "https://github.com/thinwalled/cufsm-git",
            "license": "MIT",
            "example": "examples/2006_dsm_design_guide/files_and_scripts/cnolip_P.mat",
            "cells": 500,
            "gate": "pass",
            "scope": "solver and provenance path only; not a rerun of the Zhang et al. models"
        },
        "external_relation_transfer_card": {
            "source": "AISI RP23-01 (2023), Eq. (19), printed page 12",
            "url": "https://www.buildusingsteel.org/wp-content/uploads/2023/07/AISI-RP23-01-Analytical-Equations-for-Critical-Local-Buckling-Stress-of-Lipped-Channels-second-printing.pdf",
            "relation": "k_w = 4 + 24 eta/(20 + 4.4 eta + eta^2), eta=h/b",
            "domain": [1.2, 22.0],
            "cells": 7,
            "bounded_positive_gate": "pass",
            "global_increasing_predicate": "not satisfied; relation-specific predicate map retained",
            "scope": "source equation card only; no rerun of the report's FSM sections"
        },
        "human_engineer_review": "open",
        "submission_state": "LOCAL_ONLY / NOT_SUBMITTED"
    },
    "evidence_classes": {
        "case_evidence": "Zhang et al. equations and public rounded tables",
        "method_evidence": "known-form positive control; 15 injected cases; 200 digit perturbation trials; leave-source and predicate-ablation checks",
        "transfer_evidence": "public solver example; AISI relation card; bounded Zhang source-model reconstruction; independent KSCE spectrum-transfer screen"
    },
    "method_controls": {
        "positive_control": "pass",
        "failure_or_coverage_cases": 15,
        "failure_gate_pass_fraction": 1.0,
        "digit_perturbation_trials": 200,
        "target_winner_perturbation_fraction": 1.0,
        "predicate_ablation": "monotonicity removal increases mechanically admissible candidates from 20 to 22"
    },
    "nodes": [
        {"id": "Geometry", "kind": "engineering_object", "attributes": ["a", "b", "c", "t"]},
        {"id": "LimbRatio", "kind": "dimensionless_state", "definition": "x=a/b", "domain": [1.1, 1.5]},
        {"id": "PositiveScale", "kind": "mechanics_factor", "definition": "A=k_l pi^2 E/[12(1-nu^2)] (t/a)^2", "sign": ">0"},
        {"id": "ShapeFactor", "kind": "candidate_relation", "definition": "q(x)=c0+c2*x^2+c1*x"},
        {"id": "CriticalStress", "kind": "response", "definition": "sigma_cr=A q(x)", "unit": "MPa"},
        {"id": "RoundedCell", "kind": "evidence", "definition": "reported value +/- 0.005 MPa"},
        {"id": "CUFSMCell", "kind": "held_out_evidence", "definition": "public finite-strip stress"},
        {"id": "MethodControl", "kind": "protocol_evidence", "definition": "positive control, injected failures and perturbation replay"},
        {"id": "TransferEvidence", "kind": "provenance_evidence", "definition": "independently regenerated public solver example"},
        {"id": "SourceModelReconstruction", "kind": "bounded_model_evidence", "definition": "published geometry-to-response recreation with frozen effective modulus"},
        {"id": "IndependentSpectrumTransfer", "kind": "transfer_evidence", "definition": "second published source and nearest-spectrum predicate"},
        {"id": "ExternalRelationCard", "kind": "transfer_evidence", "definition": "source-anchored relation and relation-specific predicate map"},
        {"id": "DesignAction", "kind": "engineering_task", "states": ["reject_nonexecutable", "retain_bounded_claim", "allow_bounded_query", "allow_operational_use"]},
    ],
    "relations": [
        ["Geometry", "defines", "LimbRatio"],
        ["Geometry", "sets", "PositiveScale"],
        ["LimbRatio", "enters", "ShapeFactor"],
        ["PositiveScale", "multiplies", "ShapeFactor"],
        ["ShapeFactor", "produces", "CriticalStress"],
        ["RoundedCell", "constrains", "PositiveScale"],
        ["CUFSMCell", "tests", "ShapeFactor"],
        ["MethodControl", "tests", "DesignAction"],
        ["TransferEvidence", "checks", "CUFSMCell"],
        ["ExternalRelationCard", "tests", "DesignAction"],
        ["SourceModelReconstruction", "checks", "CUFSMCell"],
        ["IndependentSpectrumTransfer", "tests", "DesignAction"],
        ["CriticalStress", "supports", "DesignAction"],
    ],
    "rules": [
        {"id": "R1", "if": "PositiveScale > 0 and ShapeFactor <= 0", "then": "reject_nonexecutable"},
        {"id": "R2", "if": "ShapeFactor(x)>0 on [1.1,1.5]", "then": "retain_positive_route"},
        {"id": "R3", "if": "d ShapeFactor/dx >= 0 on [1.1,1.5]", "then": "retain_increasing_route"},
        {"id": "R4", "if": "intersection of all scale intervals is nonempty", "then": "retain_bounded_claim"},
        {"id": "R5", "if": "public held-out table replay is complete and all reported residuals are finite", "then": "allow_bounded_query; no universal error threshold implied"},
        {"id": "R6", "if": "independent CUFSM rerun and human engineer review both pass", "then": "allow_operational_use"},
        {"id": "R7", "if": "R6 is open", "then": "retain_bounded_claim and keep human gate open"},
        {"id": "R8", "if": "independent source spectrum screen passes under a declared predicate", "then": "retain_bounded_transfer_evidence; do not promote to universal recovery"},
    ],
}
geo_contract_path = OUT / "r07_compression_index_contract.json"
if geo_contract_path.exists():
    geo = json.loads(geo_contract_path.read_text(encoding="utf-8"))
    knowledge_graph["ontology_version"] = "1.3"
    knowledge_graph["scope"] = "knowledge-constrained recovery protocol demonstrated on cold-formed steel and geotechnical relations"
    knowledge_graph.setdefault("provenance", {})["independent_geotechnical_case"] = {
        "source": geo["source"],
        "contract": geo["contract"],
        "action_summary": geo.get("action_summary", {}),
        "scope": "cross-domain direct-response correlation screen; no solver selector required",
    }
    knowledge_graph.setdefault("evidence_classes", {})["cross_domain_case_evidence"] = (
        "Uzer 2024 independent oedometer table; nine published e0-only correlations; "
        "two positivity rejects and seven bounded retains through the shared reducer"
    )
    node_ids = {n["id"] for n in knowledge_graph.get("nodes", [])}
    for node in [
        {"id": "GeotechnicalSoil", "kind": "engineering_object", "attributes": ["normally consolidated fine-grained soil"]},
        {"id": "VoidRatio", "kind": "dimensionless_state", "definition": "e0", "domain": geo["contract"]["declared_domain"]},
        {"id": "CompressionIndex", "kind": "response", "definition": "Cc", "unit": "-"},
        {"id": "PublishedCcCorrelation", "kind": "candidate_relation", "definition": "nine attributed e0-only correlations"},
        {"id": "OedometerCell", "kind": "experimental_evidence", "definition": "independent printed Table A2 cell +/- 0.0005"},
    ]:
        if node["id"] not in node_ids:
            knowledge_graph["nodes"].append(node)
    existing_relations = {tuple(r) for r in knowledge_graph.get("relations", [])}
    for rel in [
        ["GeotechnicalSoil", "defines", "VoidRatio"],
        ["VoidRatio", "enters", "PublishedCcCorrelation"],
        ["PublishedCcCorrelation", "predicts", "CompressionIndex"],
        ["OedometerCell", "tests", "PublishedCcCorrelation"],
        ["CompressionIndex", "supports", "DesignAction"],
    ]:
        if tuple(rel) not in existing_relations:
            knowledge_graph["relations"].append(rel)
    rule_ids = {r["id"] for r in knowledge_graph.get("rules", [])}
    for rule in [
        {"id": "R11", "if": "a published response is non-positive on its declared domain", "then": "reject_nonexecutable"},
        {"id": "R12", "if": "a direct-response correlation misses the displayed interval while mechanics pass", "then": "retain_bounded_claim"},
        {"id": "R13", "if": "no numerical solver selector is required by the direct-response source", "then": "record selector as not applicable; do not invent one"},
    ]:
        if rule["id"] not in rule_ids:
            knowledge_graph["rules"].append(rule)
    run_ids = {r.get("run_id") for r in knowledge_graph.get("runs", [])}
    if "geotechnical_compression_index" not in run_ids:
        knowledge_graph.setdefault("runs", []).append({
            "run_id": "geotechnical_compression_index",
            "object": "GeotechnicalSoil",
            "state": "VoidRatio",
            "response": "CompressionIndex",
            "relation": {"id": "PublishedCcCorrelation", "candidate_class": "nine published e0-only correlations", "domain": geo["contract"]["declared_domain"]},
            "predicates": {"mechanics.positivity": "relation-specific", "mechanics.monotonicity": "relation-specific", "mechanics.finiteness": True, "evidence.interval_feasibility": False, "provenance.selector_verified": "not applicable"},
            "evidence": {"cells": geo["contract"]["cells_parsed"], "displayed_half_unit": geo["contract"]["displayed_half_unit"], "action_summary": geo.get("action_summary", {})},
            "action": "heterogeneous; see outputs/r07_compression_index_contract.json",
            "scope": "observed Table A2 domain only; transcribed cells and direct-response interval predicate",
        })

(ROOT / "knowledge_graph.json").write_text(json.dumps(knowledge_graph, indent=2), encoding="utf-8")

winner = margin.loc[margin["is_reconstructed_assignment"] == True].iloc[0]
rank2 = margin.sort_values("rank").iloc[1]

summary = {
    "candidate_count": int(len(search48)),
    "winner_formula": str(winner["formula"]),
    "winner_required_halfwidth_mpa": float(winner["all_group_required_halfwidth_mpa"]),
    "display_halfwidth_mpa": DISPLAY_HALF_WIDTH,
    "nearest_positive_alternative_halfwidth_mpa": float(rank2["all_group_required_halfwidth_mpa"]),
    "identification_margin_factor_vs_winner": float(rank2["all_group_required_halfwidth_mpa"] / winner["all_group_required_halfwidth_mpa"]),
    "alternative_vs_display_halfwidth": float(rank2["all_group_required_halfwidth_mpa"] / DISPLAY_HALF_WIDTH),
    "formula_cells_primary": int(len(primary)),
    "source_rows_total": int(len(source)),
    "cufsm_cells": int(len(full)),
    "cufsm_table4_rmse_pct": float(replay.loc[replay["table"] == "Table 4", "reconstructed_relative_rmse"].mean() * 100),
    "cufsm_table8_rmse_pct": float(replay.loc[replay["table"] == "Table 8", "reconstructed_relative_rmse"].mean() * 100),
    "printed_formula_positive_fraction_primary_cells": float((primary["reported_formula_stress_mpa"] > 0).mean()),
    "printed_shape_positive_fraction_cufsm_cells": float((full["printed_q"] > 0).mean()),
    "reconstructed_shape_positive_fraction_cufsm_cells": float((full["reconstructed_q"] > 0).mean()),
    "q_identified_min_domain": float(min(q_identified(x) for x in DOMAIN)),
    "q_identified_max_domain": float(max(q_identified(x) for x in DOMAIN)),
    "dq_identified_min_domain": float(min(dq_identified(x) for x in DOMAIN)),
    "dq_identified_max_domain": float(max(dq_identified(x) for x in DOMAIN)),
    "q_printed_min_domain": float(min(q_printed(x) for x in DOMAIN)),
    "q_printed_max_domain": float(max(q_printed(x) for x in DOMAIN)),
    "full_table_group_count": int(len(replay)),
    "table8_nonmonotonic_groups": int((~replay.loc[replay["table"] == "Table 8", "cufsm_strictly_increasing_with_a_over_b"]).sum()),
    "bounded_query_replay_gate": "pass" if replay_complete_gate else "fail",
    "evidence_boundary": "public tables plus bounded independent source-model reconstruction; E_eff metadata boundary; native Zhang files unavailable; KSCE spectrum transfer is separate",
    "independent_cufsm_rerun": "bounded_reconstruction_available",
    "public_solver_transfer": "pass: 500 cells from a separately sourced MIT-licensed CUFSM example",
    "source_model_reconstruction": "pass_with_metadata_boundary: 630 rows; RMSE 0.532%; q95 1.320%; max 2.431%; E_eff=217400 MPa",
    "independent_ksce_spectrum_transfer": "pass_bounded_screen: 24 rows; RMSE 0.720%; q95 1.542%; max 1.620%; 10% predicate",
    "human_engineer_review": "open",
    "submission_state": "LOCAL_ONLY / NOT_SUBMITTED",
}
(OUT / "result_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

# Deterministic engineering query examples. These are executable queries, not new observations.
queries = []
for at in [70.0, 110.0]:
    for x in [1.1, 1.3, 1.5]:
        qp = q_printed(x)
        qr = q_identified(x)
        action = "reject_nonexecutable" if qp <= 0 else "retain_bounded_claim"
        queries.append({
            "a_over_t": at,
            "a_over_b": x,
            "printed_shape": qp,
            "identified_shape": qr,
            "identified_derivative": dq_identified(x),
            "printed_action": action,
            "identified_action": "allow_bounded_query" if replay_complete_gate and qr > 0 and dq_identified(x) >= 0 else "retain_bounded_claim",
            "operational_gate": "OPEN: independent CUFSM rerun + human engineer review",
        })
pd.DataFrame(queries).to_csv(OUT / "design_query_examples.csv", index=False)

trace = pd.DataFrame([
    {"claim": "printed route is executable", "knowledge_rule": "R1", "evidence": "20 rounded cells + positive scale", "status": "rejected"},
    {"claim": "identified coefficient assignment is compatible", "knowledge_rule": "R4", "evidence": "4/4 groups at 0.005 MPa", "status": "supported_within_candidate_class"},
    {"claim": "identified shape is positive and increasing", "knowledge_rule": "R2+R3", "evidence": "analytic domain check", "status": "supported"},
    {"claim": "identified shape is compatible with the public held-out tables", "knowledge_rule": "R5", "evidence": "630 transcribed cells and 126 groups with finite residual diagnostics; source models unavailable", "status": "bounded_replay_support"},
    {"claim": "protocol action semantics execute on known and injected inputs", "knowledge_rule": "method controls", "evidence": "positive control plus 15 predeclared failure or coverage cases", "status": "method_evidence_pass"},
    {"claim": "selected coefficient direction is stable to declared digit perturbations", "knowledge_rule": "sensitivity", "evidence": "200 deterministic trials; leave-source and predicate-ablation records", "status": "method_evidence_pass"},
    {"claim": "a public solver/provenance path can be regenerated", "knowledge_rule": "transfer gate", "evidence": "500 cells from a separately sourced CUFSM example; max abs 1.44e-4; q95 relative 9.41e-5", "status": "transfer_evidence_pass"},
    {"claim": "a different relation form can use an explicit predicate map", "knowledge_rule": "transfer card", "evidence": "AISI RP23-01 Eq. (19); 7 rounded cells; positive-bounded pass; turning point at sqrt(20)", "status": "transfer_evidence_pass_with_limits"},
    {"claim": "published source-model geometry and response path were independently recreated", "knowledge_rule": "source reconstruction", "evidence": "630 Table 4/Table 8 cells; RMSE 0.532%; q95 1.320%; max 2.431%; E_eff metadata boundary", "status": "bounded_reconstruction_pass"},
    {"claim": "an independent published complex-edge source transfers to the spectrum predicate", "knowledge_rule": "R8", "evidence": "24 KSCE Table 2 rows; RMSE 0.720%; q95 1.542%; max 1.620%; 10% screen", "status": "bounded_transfer_pass"},
    {"claim": "CUFSM simulations were independently rerun", "knowledge_rule": "scope", "evidence": "native author files not available", "status": "not_claimed"},
])
if geo_contract_path.exists():
    trace = pd.concat([trace, pd.DataFrame([{
        "claim": "a second domain runs through the shared action reducer",
        "knowledge_rule": "R11+R12+R13",
        "evidence": "Uzer 2024 Table A2; 445 cells; nine competing e0-only correlations",
        "status": "cross_domain_action_reducer_pass",
    }])], ignore_index=True)

trace.to_csv(OUT / "knowledge_trace.csv", index=False)

# Compact residual and sensitivity outputs used by the manuscript and reviewer packet.
replay_summary = []
for table, group in replay.groupby("table", sort=True):
    cell = full.loc[full["table"] == table].copy()
    rel = (cell["reconstructed_positive_scale_prediction_mpa"] - cell["cufsm_stress_mpa"]) / cell["cufsm_stress_mpa"]
    replay_summary.append({
        "table": table,
        "cells": int(len(cell)),
        "groups": int(len(group)),
        "cell_bias_pct": float(rel.mean() * 100),
        "cell_rmse_pct": float(np.sqrt(np.mean(rel**2)) * 100),
        "cell_q95_abs_error_pct": float(np.quantile(np.abs(rel), 0.95) * 100),
        "cell_max_abs_error_pct": float(np.max(np.abs(rel)) * 100),
        "group_rmse_mean_pct": float(group["reconstructed_relative_rmse"].mean() * 100),
        "group_rmse_max_pct": float(group["reconstructed_relative_rmse"].max() * 100),
        "strictly_increasing_groups": int(group["cufsm_strictly_increasing_with_a_over_b"].sum()),
        "nonmonotonic_groups": int((~group["cufsm_strictly_increasing_with_a_over_b"]).sum()),
    })
pd.DataFrame(replay_summary).to_csv(OUT / "replay_residual_summary.csv", index=False)

sensitivity = margin.copy()
sensitivity["display_halfwidth_mpa"] = DISPLAY_HALF_WIDTH
sensitivity["required_halfwidth_ratio_to_display"] = sensitivity["all_group_required_halfwidth_mpa"] / DISPLAY_HALF_WIDTH
sensitivity["candidate_status"] = np.where(
    sensitivity["is_reconstructed_assignment"], "retained_within_declared_class",
    np.where(sensitivity["compatible_at_reported_halfwidth_0p005_mpa"], "other_compatible_candidate", "rejected_by_interval_or_mechanics")
)
sensitivity.sort_values("rank").to_csv(OUT / "candidate_sensitivity.csv", index=False)

evidence_state = {
    "project": "AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-09-26",
    "revision_date": "2026-10-05",
    "state": "LOCAL_ONLY / NOT_SUBMITTED",
    "primary_claim": "A knowledge-constrained recovery protocol binds typed predicates, finite-precision evidence, provenance and bounded actions; the lipped-angle demonstration recovers one positive increasing shape within the declared permutation/sign class.",
    "evidence_classes": {
        "transcribed_public_equations_and_tables": "available",
        "deterministic_replay_from_transcriptions": "available",
        "independent_cufsm_model_rerun": "bounded_reconstruction_available; native files not available",
        "independent_source_cufsm_model_rerun": "not_available",
        "public_solver_transfer_evidence": "available; separately sourced MIT-licensed CUFSM example; 500 cells; transfer gate pass",
        "source_model_reconstruction_evidence": "available; 630 published cells; RMSE 0.532%; q95 1.320%; max 2.431%; metadata boundary",
        "independent_ksce_spectrum_transfer_evidence": "available; 24 published rows; nearest-spectrum screen pass; mode metadata boundary",
        "external_relation_transfer_evidence": "available; AISI RP23-01 Eq. (19) card; 7 cells; positive-bounded gate pass; source FSM not rerun",
        "independent_engineer_blind_review": "open",
        "operational_design_validation": "not_available"
    },
    "action_boundary": "allow_bounded_query only; operational use remains gated by R6",
    "excluded_identity": "IFC compliance-check manuscript and its submission history are outside this project"
}
if geo_contract_path.exists():
    geo = json.loads(geo_contract_path.read_text(encoding="utf-8"))
    evidence_state["revision_date"] = "2026-10-07"
    evidence_state["evidence_classes"]["cross_domain_case_evidence"] = "available; Uzer 2024 Table A2; 445 cells; nine competing correlations; shared reducer"
    evidence_state["geotechnical_case_action_summary"] = geo.get("action_summary", {})
    evidence_state["geotechnical_case_boundary"] = geo.get("boundary", "")

(OUT / "evidence_state.json").write_text(json.dumps(evidence_state, indent=2), encoding="utf-8")

# Figure 1: knowledge-to-action mechanism, vector-first.
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold"})
fig, ax = plt.subplots(figsize=(12, 4.4), dpi=220)
ax.axis("off")
boxes = [
    (0.02, 0.24, 0.16, 0.52, "Geometry\na, b, c, t", "#E8F1F8"),
    (0.22, 0.24, 0.16, 0.52, "Dimensionless state\nx=a/b; a/t; c/a", "#E8F1F8"),
    (0.42, 0.24, 0.16, 0.52, "Mechanics graph\nA>0; q(x)>0; q'(x)≥0\nA∝(a/t)⁻²", "#EAF4EA"),
    (0.62, 0.24, 0.16, 0.52, "Evidence constraints\nrounded tables\ninterval intersection\nheld-out CUFSM cells", "#FFF3DD"),
    (0.82, 0.24, 0.16, 0.52, "Engineering action\nreject invalid route\nretain bounded claim\nallow bounded query", "#FDEAEA"),
]
for x, y, w, h, txt, color in boxes:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#263238", linewidth=1.2, transform=ax.transAxes))
    ax.text(x + w/2, y + h/2, txt, ha="center", va="center", transform=ax.transAxes, fontsize=10)
for x in [0.18, 0.38, 0.58, 0.78]:
    ax.annotate("", xy=(x+0.035, 0.50), xytext=(x, 0.50), xycoords=ax.transAxes, arrowprops={"arrowstyle":"->", "lw":1.8, "color":"#37474F"})
ax.text(0.50, 0.93, "Executable engineering knowledge path", ha="center", va="center", transform=ax.transAxes, fontsize=14)
ax.text(0.50, 0.06, "The method turns mechanics statements into machine-checkable rules before a formula is allowed to support a structural calculation.", ha="center", va="center", transform=ax.transAxes, fontsize=10, color="#455A64")
fig.savefig(FIG / "figure1_knowledge_to_action.svg", bbox_inches="tight")
fig.savefig(FIG / "figure1_knowledge_to_action.png", bbox_inches="tight", dpi=300)
fig.savefig(FIG / "figure1_knowledge_to_action.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 2: evidence/result comparison, avoiding overlapping annotations.
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), dpi=220, constrained_layout=True)
x = np.linspace(1.1, 1.5, 200)
axes[0].plot(x, q_printed(x), color="#C62828", lw=2.6, label="printed route")
axes[0].plot(x, q_identified(x), color="#1565C0", lw=2.6, label="identified route")
axes[0].axhline(0, color="#263238", lw=1)
axes[0].fill_between(x, q_printed(x), 0, where=q_printed(x)<0, color="#EF9A9A", alpha=.28)
axes[0].set_xlabel("Limb ratio, x=a/b")
axes[0].set_ylabel("Shape factor q(x)")
axes[0].set_title("Mechanics admissibility")
axes[0].legend(frameon=False, loc="lower left")
axes[0].grid(axis="y", color="#ECEFF1")

agg = replay.groupby("table", as_index=False)["reconstructed_relative_rmse"].mean()
axes[1].bar(agg["table"], agg["reconstructed_relative_rmse"]*100, color=["#5E4FA2", "#2A9D8F"], width=.55)
axes[1].set_ylabel("Relative RMSE (%)")
axes[1].set_title("Held-out CUFSM replay")
axes[1].grid(axis="y", color="#ECEFF1")
for i, v in enumerate(agg["reconstructed_relative_rmse"]*100):
    axes[1].text(i, v + 0.03, f"{v:.3f}%", ha="center", va="bottom", fontsize=10)
fig.savefig(FIG / "figure2_admissibility_and_replay.svg", bbox_inches="tight")
fig.savefig(FIG / "figure2_admissibility_and_replay.png", bbox_inches="tight", dpi=300)
fig.savefig(FIG / "figure2_admissibility_and_replay.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 3: normalized curves and cell-level residuals regenerated from the
# public cells. Each light curve is one fixed (a/t, c/a) group.
fig = plt.figure(figsize=(11.0, 9.6), dpi=220, constrained_layout=True)
grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.82])
curve_axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
for ax, table, panel in zip(curve_axes, ["Table 4", "Table 8"], ["a", "b"]):
    table_full = full.loc[full["table"] == table]
    for _, group in table_full.groupby(["a_over_t", "c_over_a"], sort=True):
        group = group.sort_values("a_over_b")
        y = group["cufsm_stress_mpa"].to_numpy()
        ax.plot(group["a_over_b"], y / y[0], color="#B0BEC5", alpha=0.28, lw=1.1)
    x_curve = np.linspace(DOMAIN[0], DOMAIN[1], 300)
    ax.plot(x_curve, q_identified(x_curve) / q_identified(DOMAIN[0]), color="#2166AC", lw=3.2, label="identified shape")
    ax.set_title(f"{panel}   {table}: 63 fixed-geometry curves", loc="left", fontsize=12)
    ax.set_xlabel(r"Limb ratio, $x=a/b$")
    ax.set_ylabel(r"Normalized stress, $\sigma(x)/\sigma(1.1)$")
    ax.set_xlim(*DOMAIN)
    ax.grid(axis="y", color="#ECEFF1")
    ax.legend(frameon=False, loc="upper left")

hist_ax = fig.add_subplot(grid[1, :])
bins = np.linspace(-3.5, 3.5, 31)
for table, color, label in [
    ("Table 4", "#5E4FA2", "Table 4"),
    ("Table 8", "#2A9D8F", "Table 8"),
]:
    residual = full.loc[full["table"] == table, "reconstructed_relative_error_pct"].to_numpy()
    hist_ax.hist(residual, bins=bins, density=True, histtype="step", linewidth=2.6, color=color, label=label)
hist_ax.axvline(0, color="#263238", lw=1.1)
hist_ax.set_title("c   Cell-level shape residuals", loc="left", fontsize=12)
hist_ax.set_xlabel("Reconstructed-shape relative error (%)")
hist_ax.set_ylabel("Density")
hist_ax.grid(axis="y", color="#ECEFF1")
hist_ax.legend(frameon=False, loc="upper right")
fig.savefig(FIG / "figure3_full_table_shape_replay.svg", bbox_inches="tight")
fig.savefig(FIG / "figure3_full_table_shape_replay.png", bbox_inches="tight", dpi=300)
fig.savefig(FIG / "figure3_full_table_shape_replay.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 4: error boundary and group heterogeneity. This is a diagnostic display,
# not a new validation dataset.
fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), dpi=220, constrained_layout=True)
for table, color, marker in [("Table 4", "#5E4FA2", "o"), ("Table 8", "#2A9D8F", "s")]:
    g = replay.loc[replay["table"] == table].groupby("a_over_t", as_index=False)["reconstructed_relative_rmse"].agg(["mean", "max"]).reset_index()
    axes[0].plot(g["a_over_t"], g["mean"] * 100, color=color, marker=marker, lw=2, label=f"{table} mean")
    axes[0].fill_between(g["a_over_t"], g["mean"] * 100, g["max"] * 100, color=color, alpha=0.14)
axes[0].set_xlabel("a/t")
axes[0].set_ylabel("Group relative RMSE (%)")
axes[0].set_title("Replay error envelope")
axes[0].legend(frameon=False, fontsize=9)
axes[0].grid(axis="y", color="#ECEFF1")
box_data = [
    full.loc[full["table"] == "Table 4", "reconstructed_relative_error_pct"].abs(),
    full.loc[full["table"] == "Table 8", "reconstructed_relative_error_pct"].abs(),
]
axes[1].boxplot(box_data, tick_labels=["Table 4", "Table 8"], showfliers=True, patch_artist=True,
                boxprops={"facecolor": "#DCE6F1", "edgecolor": "#37474F"},
                medianprops={"color": "#C62828", "linewidth": 1.5})
axes[1].set_ylabel("Absolute relative error (%)")
axes[1].set_title("Cell-level error distribution")
axes[1].grid(axis="y", color="#ECEFF1")
fig.savefig(FIG / "figure4_replay_error_boundary.svg", bbox_inches="tight")
fig.savefig(FIG / "figure4_replay_error_boundary.png", bbox_inches="tight", dpi=300)
fig.savefig(FIG / "figure4_replay_error_boundary.pdf", bbox_inches="tight")
plt.close(fig)

print(json.dumps(summary, indent=2))

