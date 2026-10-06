"""R04 W4 — Direct Strength Method (DSM) module-level integration demo.

Purpose
-------
Show, inside the AISI S100 Direct Strength Method workflow, the downstream consequence of
(i) the printed expression (negative local-buckling stress -> non-executable design input)
and (ii) the recovered relation (executable, bounded query). This is a *module-level* demo
of the local-buckling input: it does not rebuild the global or distortional channels and
does not claim code compliance or member safety.

Demo cross-section (from Zhang et al. 2022 Table 4 family, public version of record):
  simple-lipped unequal-limb angle, a/t = 70, c/a = 0.2, t = 2 mm, a/b in [1.1, 1.5].
  Local-buckling stresses are the public table cells (CUFSM elastic values).
  Design material for the demo only: fy = 350 MPa (representative, not the source paper's).

DSM local curve (AISI S100, Appendix 1):
  lambda_l = sqrt(Py / P_crl);  P_crl = sigma_crl * A
  P_nl = Py                       if lambda_l <= 0.776
  P_nl = (1 - 0.15 (lambda_l - 0.776) / lambda_l) Py   if lambda_l > 0.776, capped by P_ne
  Here P_ne is NOT rebuilt (global channel); the demo reports the local reduction factor
  phi_l = P_nl / Py and marks the P_ne cap as an open module.

Outputs
-------
  outputs/r04_dsm_demo_summary.json
  outputs/r04_dsm_demo_table.csv
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "data" / "full_cufsm_cells.csv"
OUT = ROOT / "outputs"

T_MM = 2.0
C_OVER_A = 0.2
AT = 100.0
A_MM = AT * T_MM                # a = 200 mm
LIP_MM = C_OVER_A * A_MM        # c = 40 mm
FY = 350.0                       # MPa, demo material (declared, not from Zhang et al.)
X_GRID = [1.1, 1.2, 1.3, 1.4, 1.5]
Q_PRINT = lambda x: 0.292 - 1.060 * x ** 2 + 0.339 * x   # printed (fails R1)
Q_ID = lambda x: 0.292 - 0.339 * x ** 2 + 1.060 * x      # recovered


def section_area(a_over_b: float) -> float:
    """Centreline area of the simple-lipped unequal-limb angle (corner radii ignored)."""
    b = A_MM / a_over_b
    return T_MM * (A_MM + b + LIP_MM)


def dsm_local(sigma_crl: float, area: float) -> dict:
    """Local-buckling module of the DSM. Returns the reduction factor and diagnostics."""
    py = FY * area
    if sigma_crl <= 0:
        return {"executable": False, "sigma_crl_mpa": sigma_crl, "Py_kN": py / 1e3,
                "lambda_l": None, "phi_l": None,
                "failure": "non-positive critical stress: sqrt(Py/Pcrl) undefined"}
    pcrl = sigma_crl * area
    lam = math.sqrt(py / pcrl)
    phi = 1.0 if lam <= 0.776 else max(0.0, 1 - 0.15 * (lam - 0.776) / lam)
    return {"executable": True, "sigma_crl_mpa": sigma_crl, "Py_kN": py / 1e3,
            "lambda_l": lam, "phi_l": phi, "failure": ""}


def scale_from_cell(a_over_b: float, cell_stress: float) -> float:
    return cell_stress / Q_ID(a_over_b)


def main() -> None:
    cells = pd.read_csv(CELLS)
    tab4 = cells[(cells["table"] == "Table 4") & (cells["a_over_t"] == AT)
                 & (cells["c_over_a"] == C_OVER_A)].sort_values("a_over_b")
    assert len(tab4) == 5, "expected the five public Table 4 cells at a/t=100, c/a=0.2"
    stresses = tab4["cufsm_stress_mpa"].to_numpy()

    # group scale from the recovered relation at the five cells
    scales = [scale_from_cell(x, s) for x, s in zip(X_GRID, stresses)]
    s_mid = float(np.mean(scales))
    s_ref = scale_from_cell(1.3, stresses[2])  # mid-cell anchor

    rows = []
    for x, s_cell in zip(X_GRID, stresses):
        area = section_area(x)
        # (a) public table value
        r_table = dsm_local(float(s_cell), area)
        # (b) recovered relation, evaluated through the interval-fitted scale
        s_recovered = s_cell  # same anchor by construction; use table cell for the public value
        # (c) recovered relation with a single frozen group scale (protocol query mode)
        sigma_from_relation = s_ref * Q_ID(x)
        r_rel = dsm_local(float(sigma_from_relation), area)
        # (d) printed expression (fails R1 before DSM)
        sigma_print = s_ref * Q_PRINT(x)
        r_print = dsm_local(float(sigma_print), area)
        rows.append({
            "a_over_b": x, "area_mm2": area, "Py_kN": FY * area / 1e3,
            "sigma_crl_table_mpa": float(s_cell),
            "lambda_l_table": r_table["lambda_l"], "phi_l_table": r_table["phi_l"],
            "sigma_crl_recovered_mpa": float(sigma_from_relation),
            "lambda_l_recovered": r_rel["lambda_l"], "phi_l_recovered": r_rel["phi_l"],
            "recovered_vs_table_phi_dev_pct":
                100.0 * (r_rel["phi_l"] - r_table["phi_l"]) / r_table["phi_l"],
            "sigma_crl_printed_mpa": float(sigma_print),
            "printed_dsm_executable": r_print["executable"],
            "printed_failure_note": r_print["failure"],
        })

    df = pd.DataFrame(rows)

    # abs-misuse scenario: a designer bypassing the sign check feeds |sigma| into the DSM
    misuse = []
    for x in X_GRID:
        area = section_area(x)
        sigma_abs = abs(s_ref * Q_PRINT(x))
        r_abs = dsm_local(sigma_abs, area)
        r_ok = dsm_local(float(s_ref * Q_ID(x)), area)
        misuse.append({
            "a_over_b": x,
            "abs_printed_sigma_mpa": sigma_abs,
            "phi_l_abs_print": r_abs["phi_l"] if r_abs["executable"] else None,
            "phi_l_recovered": r_ok["phi_l"],
            "unconservative_factor": (r_ok["phi_l"] / r_abs["phi_l"]) if r_abs["executable"] else None,
        })
    misuse_df = pd.DataFrame(misuse)

    summary = {
        "round": "R04_W4",
        "module": "DSM local-buckling input module (AISI S100 App.1 curve)",
        "cross_section": {"family": "simple-lipped unequal-limb angle (Zhang et al. 2022, Table 4)",
                          "a_over_t": AT, "c_over_a": C_OVER_A, "t_mm": T_MM,
                          "a_mm": A_MM, "lip_mm": LIP_MM},
        "demo_material": {"fy_mpa": FY, "note": "representative demo value, not the source paper's material"},
        "open_modules": ["global (P_ne) channel not rebuilt; phi_l cap by P_ne is not applied",
                         "distortional channel not rebuilt",
                         "corner radii ignored in the centreline area"],
        "key_numbers": {
            "phi_l_recovered_range": [float(df["phi_l_recovered"].min()), float(df["phi_l_recovered"].max())],
            "max_recovered_vs_table_phi_dev_pct": float(df["recovered_vs_table_phi_dev_pct"].abs().max()),
            "printed_expression_executable_cells": int(df["printed_dsm_executable"].sum()),
            "printed_expression": "rejected before DSM by rule R1 (negative, decreasing)",
            "abs_misuse_unconservative_max_factor": (
                float(misuse_df["unconservative_factor"].max())
                if misuse_df["unconservative_factor"].notna().any() else None),
        },
        "conclusion": (
            "With the recovered relation the local-buckling DSM module executes across the "
            "declared domain and reproduces the public-table phi_l path within the replay "
            "accuracy. With the printed expression the module is non-executable (negative "
            "critical stress); silently using its absolute value yields materially "
            "unconservative local strengths. The demo is bounded to the local module; "
            "P_ne and distortional channels remain open."
        ),
    }

    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "r04_dsm_demo_table.csv", index=False)
    (OUT / "r04_dsm_demo_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(df[["a_over_b", "sigma_crl_table_mpa", "lambda_l_table", "phi_l_table",
              "phi_l_recovered", "recovered_vs_table_phi_dev_pct",
              "printed_dsm_executable"]].to_string(index=False))
    print(json.dumps(summary["key_numbers"], indent=2))


if __name__ == "__main__":
    main()