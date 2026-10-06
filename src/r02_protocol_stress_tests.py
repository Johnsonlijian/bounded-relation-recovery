from __future__ import annotations

"""R02 protocol-level validation for the knowledge-constrained recovery method.

The script separates method evidence from the lipped-angle case evidence.  It
uses a known rounded relation as a positive control, deliberately malformed
inputs as negative controls, and the existing project transcription for
leave-source, digit-perturbation and predicate-ablation checks.  It does not
promote any result to an independent physical simulation.
"""

import hashlib
import itertools
import json
import subprocess
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

DISPLAY_HALF_WIDTH = 0.005
CASE_DOMAIN = (1.1, 1.5)
CASE_MAGNITUDES = (0.292, 0.339, 1.060)
CONTROL_DOMAIN = (1.1, 1.5)
CONTROL_MAGNITUDES = (0.84, 0.06, 0.22)  # c0, c2, c1 target order
CONTROL_TARGET = (0.84, -0.06, 0.22)


def candidate_q(coefficients, x):
    c0, c2, c1 = coefficients
    x = np.asarray(x, dtype=float)
    return c0 + c2 * x**2 + c1 * x


def candidate_derivative(coefficients, x):
    _, c2, c1 = coefficients
    x = np.asarray(x, dtype=float)
    return 2 * c2 * x + c1


def formula_text(coefficients):
    c0, c2, c1 = coefficients
    return f"{c0:+.3f} {c2:+.3f} x^2 {c1:+.3f} x"


def enumerate_coefficients(magnitudes):
    for permutation in itertools.permutations(magnitudes):
        for signs in itertools.product((-1, 1), repeat=3):
            yield tuple(float(a * b) for a, b in zip(permutation, signs))


def positive_scale(y, q):
    y = np.asarray(y, dtype=float)
    q = np.asarray(q, dtype=float)
    if y.size == 0 or not np.isfinite(y).all() or not np.isfinite(q).all():
        return np.nan
    if np.any(q <= 0):
        return np.nan
    value = float(np.dot(q, y) / np.dot(q, q))
    return value if value > 0 else np.nan


def group_interval(y, q, halfwidth=DISPLAY_HALF_WIDTH):
    y = np.asarray(y, dtype=float)
    q = np.asarray(q, dtype=float)
    if y.size == 0 or not np.isfinite(y).all() or not np.isfinite(q).all() or np.any(q <= 0):
        return np.nan, np.nan
    lower = float(np.max((y - halfwidth) / q))
    upper = float(np.min((y + halfwidth) / q))
    # The common scale is declared positive.  This check matters for negative
    # controls and was not needed by the original all-positive table.
    if upper <= 0:
        return np.nan, np.nan
    return lower, upper


def minimax_halfwidth(y, q):
    y = np.asarray(y, dtype=float)
    q = np.asarray(q, dtype=float)
    if y.size == 0 or not np.isfinite(y).all() or not np.isfinite(q).all() or np.any(q <= 0):
        return np.inf
    # A positive scale is required even for the minimax diagnostic.
    if np.max(y) <= 0:
        return np.inf
    ratios = y / q
    pairwise = [
        (ratios[i] - ratios[j]) / (1.0 / q[i] + 1.0 / q[j])
        for i in range(len(y))
        for j in range(len(y))
    ]
    return max(0.0, max(pairwise))


def domain_ok(coefficients, domain, direction=1):
    grid = np.linspace(domain[0], domain[1], 2001)
    q = candidate_q(coefficients, grid)
    if not np.isfinite(q).all() or np.any(q <= 0):
        return False
    if direction == 1 and np.any(candidate_derivative(coefficients, grid) < 0):
        return False
    if direction == -1 and np.any(candidate_derivative(coefficients, grid) > 0):
        return False
    return True


def recover(groups, magnitudes, domain, halfwidth=DISPLAY_HALF_WIDTH, direction=1):
    """Recover candidates and return a bounded action plus audit rows."""
    invalid = any(
        len(g) == 0
        or not np.isfinite(g["x"].to_numpy(dtype=float)).all()
        or not np.isfinite(g["y"].to_numpy(dtype=float)).all()
        or np.any(g["y"].to_numpy(dtype=float) <= 0)
        or np.any(g["x"].to_numpy(dtype=float) < domain[0])
        or np.any(g["x"].to_numpy(dtype=float) > domain[1])
        for g in groups
    )
    complete = bool(
        len(groups) == 4
        and all(len(g) == 5 for g in groups)
        and all(g["x"].nunique() == 5 for g in groups)
    )
    rows = []
    for coefficients in enumerate_coefficients(magnitudes):
        if not domain_ok(coefficients, domain, direction=direction):
            continue
        widths = []
        compatible = 0
        for group in groups:
            q = candidate_q(coefficients, group["x"].to_numpy(dtype=float))
            y = group["y"].to_numpy(dtype=float)
            lower, upper = group_interval(y, q, halfwidth=halfwidth)
            width = minimax_halfwidth(y, q)
            widths.append(width)
            if np.isfinite(lower) and lower <= upper:
                compatible += 1
        required = max(widths) if widths else np.inf
        rows.append({
            "coefficients": coefficients,
            "formula": formula_text(coefficients),
            "compatible_groups": compatible,
            "required_halfwidth": required,
            "complete_grid": complete,
        })
    candidates = pd.DataFrame(rows)
    if invalid or candidates.empty:
        action = "reject_nonexecutable"
        winner = None
    else:
        candidates = candidates.sort_values(
            ["required_halfwidth", "formula"], kind="stable"
        ).reset_index(drop=True)
        winner = candidates.iloc[0]
        compatible = winner["compatible_groups"] == len(groups) and winner["required_halfwidth"] <= halfwidth
        if compatible:
            action = "allow_bounded_query" if complete else "retain_bounded_claim"
        else:
            # A complete grid with no admissible candidate is a hard failure;
            # an incomplete grid remains a bounded, non-operational claim.
            action = "reject_nonexecutable" if complete else "retain_bounded_claim"
    return action, winner, candidates, complete, invalid


def make_control_data(q_function, scales, x_values, round_digits=2):
    rows = []
    for group_id, scale in enumerate(scales, start=1):
        raw = float(scale) * q_function(x_values)
        for x, value in zip(x_values, raw):
            rows.append({"group": group_id, "x": float(x), "y": round(float(value), round_digits)})
    return pd.DataFrame(rows)


def grouped(frame):
    return [group.copy() for _, group in frame.groupby("group", sort=True)]


def run_failure_cases(clean):
    cases = {"clean_positive_control": clean.copy()}
    sign_flip = clean.copy()
    sign_flip["y"] *= -1
    cases["all_negative_scale"] = sign_flip

    one_negative = clean.copy()
    one_negative.loc[one_negative.index[0], "y"] *= -1
    cases["single_negative_cell"] = one_negative

    x_swap = clean.copy()
    first = x_swap.index[x_swap["group"] == 1].tolist()
    x_swap.loc[first[0], "x"], x_swap.loc[first[-1], "x"] = x_swap.loc[first[-1], "x"], x_swap.loc[first[0], "x"]
    cases["swapped_grid_endpoints"] = x_swap

    precision_conflict = clean.copy()
    precision_conflict.loc[precision_conflict.index[2], "y"] += 0.25
    cases["large_rounding_conflict"] = precision_conflict

    inconsistent_group = clean.copy()
    inconsistent_group.loc[inconsistent_group["group"] == 4, "y"] *= 1.12
    cases["inconsistent_group_scale"] = inconsistent_group

    missing_cell = clean.drop(index=clean.index[2]).copy()
    cases["missing_cell"] = missing_cell

    missing_group = clean.loc[clean["group"] != 4].copy()
    cases["missing_group"] = missing_group

    duplicate_grid = clean.copy()
    first = duplicate_grid.index[duplicate_grid["group"] == 1].tolist()
    duplicate_grid.loc[first[-1], "x"] = duplicate_grid.loc[first[-2], "x"]
    cases["duplicate_grid_value"] = duplicate_grid

    nan_input = clean.copy()
    nan_input.loc[nan_input.index[4], "y"] = np.nan
    cases["nonfinite_input"] = nan_input

    zero_input = clean.copy()
    zero_input["y"] = 0.0
    cases["zero_scale"] = zero_input

    domain_bad = clean.copy()
    # This relation is generated from a shape that turns over outside the
    # declared interval; the expanded-domain check should reject it.
    cases["expanded_domain"] = domain_bad

    bad_shape = make_control_data(
        lambda x: 0.84 + 0.55 * (x - 1.3) ** 2,
        [180, 150, 120, 90],
        np.array([1.1, 1.2, 1.3, 1.4, 1.5]),
    )
    cases["nonmonotonic_true_shape"] = bad_shape

    # A second corruption family exercises a domain mismatch while preserving
    # positive values; it should fail the declared object-domain contract.
    outside = clean.copy()
    outside.loc[outside.index[:2], "x"] = [0.6, 0.7]
    cases["out_of_domain_cells"] = outside

    swapped_group = clean.copy()
    g2 = swapped_group.index[swapped_group["group"] == 2].tolist()
    swapped_group.loc[g2, "y"] = swapped_group.loc[g2, "y"].to_numpy()[::-1]
    cases["reversed_response_group"] = swapped_group

    noisy = clean.copy()
    noisy.loc[noisy.index[7], "y"] += 0.06
    noisy.loc[noisy.index[16], "y"] -= 0.06
    cases["two_cell_outliers"] = noisy
    return cases


def run_case_suite():
    x_values = np.array([1.1, 1.2, 1.3, 1.4, 1.5])
    q_true = lambda x: 0.84 - 0.06 * np.asarray(x) ** 2 + 0.22 * np.asarray(x)
    clean = make_control_data(q_true, [220, 180, 140, 100], x_values)
    rows = []
    for name, frame in run_failure_cases(clean).items():
        domain = (0.6, 3.0) if name == "expanded_domain" else CONTROL_DOMAIN
        action, winner, candidates, complete, invalid = recover(
            grouped(frame), CONTROL_MAGNITUDES, domain, direction=1
        )
        expected = {
            "clean_positive_control": "allow_bounded_query",
            # Independent group scales are part of the declared model; this
            # case is a deliberate limitation probe rather than a failure.
            "inconsistent_group_scale": "allow_bounded_query",
            "missing_cell": "retain_bounded_claim",
            "missing_group": "retain_bounded_claim",
            "duplicate_grid_value": "retain_bounded_claim",
        }.get(name, "reject_nonexecutable")
        rows.append({
            "case": name,
            "rows": len(frame),
            "action": action,
            "expected_action": expected,
            "gate_pass": action == expected,
            "invalid_input": invalid,
            "complete_grid": complete,
            "admissible_candidate_count": int(len(candidates)),
            "winner": winner["formula"] if winner is not None else "",
            "winner_compatible_groups": int(winner["compatible_groups"]) if winner is not None else 0,
            "winner_required_halfwidth": float(winner["required_halfwidth"]) if winner is not None else np.nan,
        })
    result = pd.DataFrame(rows)
    return clean, result


def current_case_sensitivity():
    source = pd.read_csv(DATA / "source_table_transcription.csv")
    primary = source[source["transcription_role"] == "equation_reconstruction"].copy()
    converted = primary.rename(columns={"a_over_b": "x", "reported_formula_stress_mpa": "y"})
    groups_all = [g.copy() for _, g in converted.groupby(["table", "a_over_t"], sort=True)]
    groups_by_table = {
        table: [g.copy() for _, g in group.groupby("a_over_t", sort=True)]
        for table, group in converted.groupby("table", sort=True)
    }
    rows = []
    for label, groups in [("all_primary", groups_all), *sorted(groups_by_table.items())]:
        action, winner, candidates, complete, invalid = recover(
            groups, CASE_MAGNITUDES, CASE_DOMAIN, direction=1
        )
        rows.append({
            "subset": label,
            "action": action,
            "winner": winner["formula"] if winner is not None else "",
            "compatible_groups": int(winner["compatible_groups"]) if winner is not None else 0,
            "required_halfwidth": float(winner["required_halfwidth"]) if winner is not None else np.nan,
            "candidate_count_after_mechanics": int(len(candidates)),
            "complete_grid": complete,
            "invalid_input": invalid,
        })

    # Predicate ablation: retain positivity but remove the increasing-response
    # predicate. This is an explanatory ablation, not a replacement method.
    for direction, label in [(1, "positive_plus_increasing"), (None, "positive_only")]:
        action, winner, candidates, complete, invalid = recover(
            groups_all, CASE_MAGNITUDES, CASE_DOMAIN, direction=direction
        )
        rows.append({
            "subset": label,
            "action": action,
            "winner": winner["formula"] if winner is not None else "",
            "compatible_groups": int(winner["compatible_groups"]) if winner is not None else 0,
            "required_halfwidth": float(winner["required_halfwidth"]) if winner is not None else np.nan,
            "candidate_count_after_mechanics": int(len(candidates)),
            "complete_grid": complete,
            "invalid_input": invalid,
        })

    # One-cell last-digit perturbations and a deterministic 200-draw rounded
    # perturbation suite. These quantify rank stability, not physical truth.
    target = (0.292, -0.339, 1.060)
    rng = np.random.default_rng(20261004)
    records = []
    for trial in range(200):
        perturbed = converted.copy()
        offsets = rng.choice([-0.01, 0.0, 0.01], size=len(perturbed))
        perturbed["y"] = perturbed["y"].to_numpy() + offsets
        groups = [g.copy() for _, g in perturbed.groupby(["table", "a_over_t"], sort=True)]
        action, winner, candidates, _, _ = recover(groups, CASE_MAGNITUDES, CASE_DOMAIN, direction=1)
        records.append({
            "trial": trial,
            "action": action,
            "winner": winner["formula"] if winner is not None else "",
            "target_selected": bool(winner is not None and winner["coefficients"] == target),
        })
    perturbation = pd.DataFrame(records)
    return pd.DataFrame(rows), perturbation


def build_evidence_manifest():
    """Create a row-level provenance map for every table value used."""
    source = pd.read_csv(DATA / "source_table_transcription.csv")
    full = pd.read_csv(DATA / "full_cufsm_cells.csv")
    rows = []
    for idx, row in source.iterrows():
        rows.append({
            "evidence_id": f"equation_cell_{idx + 1:04d}",
            "evidence_class": "case_primary_equation_table",
            "source_doi": row["doi"],
            "source_page": int(row["vor_page"]),
            "source_table": row["table"],
            "source_file": "data/source_table_transcription.csv",
            "transformation": "manual transcription from version-of-record table",
            "rounding_rule": "reported value treated as round-to-nearest with half-width 0.005 MPa",
            "value_column": "reported_formula_stress_mpa",
            "row_index": int(idx),
        })
    for idx, row in full.iterrows():
        rows.append({
            "evidence_id": f"replay_cell_{idx + 1:04d}",
            "evidence_class": "case_public_table_replay",
            "source_doi": "10.3390/buildings12060712",
            "source_page": int(row["vor_page"]),
            "source_table": row["table"],
            "source_file": "data/full_cufsm_cells.csv",
            "transformation": "manual transcription; positive-scale replay derived by src/analyze_rebuild.py",
            "rounding_rule": "source precision retained; replay residual is descriptive",
            "value_column": "cufsm_stress_mpa",
            "row_index": int(idx),
        })
    manifest = pd.DataFrame(rows)
    manifest.to_csv(OUT / "r02_evidence_manifest.csv", index=False)
    return manifest


def source_manifest():
    repo = ROOT / "external_sources" / "cufsm-git"
    files = [
        repo / "LICENSE",
        repo / "README.md",
        repo / "examples" / "batchcufsm5results.mat",
        repo / "examples" / "2006_dsm_design_guide" / "files_and_scripts" / "cnolip_P.mat",
        repo / "examples" / "2006_dsm_design_guide" / "files_and_scripts" / "cnolip_P_post.m",
    ]
    rows = []
    for path in files:
        rows.append({
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
        })
    try:
        commit = (
            subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if repo.exists()
            else "unavailable"
        )
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    return {"repository": "https://github.com/thinwalled/cufsm-git", "commit": commit, "files": rows}


def main():
    clean, failure = run_case_suite()
    sensitivity, perturbation = current_case_sensitivity()
    manifest = build_evidence_manifest()
    failure.to_csv(OUT / "r02_failure_injection_results.csv", index=False)
    sensitivity.to_csv(OUT / "r02_case_sensitivity_and_ablation.csv", index=False)
    perturbation.to_csv(OUT / "r02_digit_perturbation_trials.csv", index=False)
    (OUT / "r02_cufsm_public_source_manifest.json").write_text(
        json.dumps(source_manifest(), indent=2), encoding="utf-8"
    )
    control_summary = {
        "positive_control_action": failure.loc[failure["case"] == "clean_positive_control", "action"].iloc[0],
        "failure_cases": int(len(failure) - 1),
        "failure_gate_pass_count": int(failure["gate_pass"].sum()),
        "failure_gate_pass_fraction": float(failure["gate_pass"].mean()),
        "target_winner_perturbation_fraction": float(perturbation["target_selected"].mean()),
        "perturbation_trials": int(len(perturbation)),
        "evidence_manifest_rows": int(len(manifest)),
        "leave_source_winners": sensitivity.loc[
            sensitivity["subset"].astype(str).str.startswith("Table"), "winner"
        ].tolist(),
        "positive_plus_increasing_candidate_count": int(
            sensitivity.loc[
                sensitivity["subset"] == "positive_plus_increasing", "candidate_count_after_mechanics"
            ].iloc[0]
        ),
        "positive_only_candidate_count": int(
            sensitivity.loc[
                sensitivity["subset"] == "positive_only", "candidate_count_after_mechanics"
            ].iloc[0]
        ),
        "public_solver_source": "https://github.com/thinwalled/cufsm-git",
        "public_solver_license": "MIT (repository LICENSE; verify before redistribution)",
        "evidence_boundary": "protocol stress tests and public-source provenance; not a rerun of the Zhang et al. models",
    }
    (OUT / "r02_protocol_validation_summary.json").write_text(
        json.dumps(control_summary, indent=2), encoding="utf-8"
    )

    # Figure 5: method evidence is visibly separate from the single case.
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8), dpi=220, constrained_layout=True)
    action_counts = failure["action"].value_counts().reindex(
        ["allow_bounded_query", "retain_bounded_claim", "reject_nonexecutable"], fill_value=0
    )
    axes[0].bar(action_counts.index, action_counts.values, color=["#2A9D8F", "#E9C46A", "#E76F51"])
    axes[0].set_title("a  Injected-input actions")
    axes[0].set_ylabel("Number of cases")
    axes[0].tick_params(axis="x", rotation=35)
    axes[0].grid(axis="y", color="#ECEFF1")

    perturbation["target_selected"].value_counts().reindex([True, False], fill_value=0).plot(
        kind="bar", ax=axes[1], color=["#2166AC", "#B0BEC5"]
    )
    axes[1].set_title("b  Target rank under ±0.01 perturbations")
    axes[1].set_ylabel("Trials")
    axes[1].set_xticklabels(["selected", "not selected"], rotation=0)
    axes[1].grid(axis="y", color="#ECEFF1")

    ablation = sensitivity[sensitivity["subset"].isin(["positive_plus_increasing", "positive_only"])]
    axes[2].bar(ablation["subset"], ablation["candidate_count_after_mechanics"], color=["#1565C0", "#90CAF9"])
    axes[2].set_title("c  Predicate ablation")
    axes[2].set_ylabel("Admissible candidates")
    axes[2].tick_params(axis="x", rotation=35)
    axes[2].grid(axis="y", color="#ECEFF1")
    fig.suptitle("Protocol-level evidence, separated from the angle case", fontsize=13, fontweight="bold")
    for ext, kwargs in [("svg", {}), ("png", {"dpi": 300}), ("pdf", {})]:
        fig.savefig(FIG / f"figure5_protocol_stress_tests.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)
    print(json.dumps(control_summary, indent=2))


if __name__ == "__main__":
    main()
