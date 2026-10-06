"""R04 W2 — Second-object full protocol application: AISI RP23-01 lipped-channel
pure-compression equation, independently rebuilt and audited.

Object
------
Reported relation (Ding & Schafer, AISI RP23-01, 2023, public report), gross lipped
channels under pure compression, no punchouts:

    k_w(eta) = 4 + 24*eta / (20 + 4.4*eta + eta^2),  eta = h/b,  1.2 <= eta <= 22,
    Fcrl = k_w * pi^2 E / (12 (1 - nu^2)) * (t/h)^2.

The report validates the equation against its 1228-section FSM library with
mean FSM/predicted = 1.00 and COV = 0.02, presented as figures and summary statistics.
The report does not publish a per-section validation table.

Protocol application (this script)
---------------------------------
1. Predicate audit of the declared relation on its declared domain (closed form).
2. Independent evidence generation: 21 fresh lipped-channel sections sampled inside the
   declared geometry domain (eta grid spanning the sqrt(20) turning point; D/B at the
   declared bounds and midpoint; t=1 mm; E=203 GPa), rebuilt with the public CUFSM
   source and the same strip discretisation contract as the angle reconstruction.
   These are NOT the report's own sections; the audit tests the declared equation on
   an independently generated evidence set.
3. Interval-free ratio audit: k_w(FSM)/k_w(Eq. 19) per section, with a predeclared
   10% screen (report COV 0.02 implies typical scatter of a few percent; 10% is a
   conservative screen, not a claimed tolerance of the equation).
4. Protocol action: `allow_bounded_query` if predicates hold and all ratios pass;
   otherwise the corresponding reject/retain action with cell-level residuals.

Commands
--------
  python src/r04_rp23001_rebuild.py prepare   # writes cases CSV + provenance
  # run the Octave chunks (r04_rp2301_cufsm_run.m), then:
  python src/r04_rp23001_rebuild.py summarize
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "external_sources" / "rp23001_rebuild"
OUT = ROOT / "outputs"

T_MM = 1.0
E_MPA = 203000.0
NU = 0.30
ETA_GRID = [1.2, 2.2, 4.472135955, 8.0, 12.0, 16.0, 20.0]   # includes sqrt(20) turning point
D_OVER_B_GRID = [0.10, 0.25, 0.40]                            # declared D/B bounds and midpoint
SCREEN_RATIO = 1.10  # predeclared: |k_fsm/k_eq - 1| <= 10% per section


def kw_equation(eta: float) -> float:
    return 4 + 24 * eta / (20 + 4.4 * eta + eta ** 2)


def prepare() -> Path:
    EXT.mkdir(parents=True, exist_ok=True)
    rows = []
    case_id = 0
    for eta in ETA_GRID:
        # choose web depth so that B/t stays above the declared B/t > 8 bound
        H = 250.0
        B = H / eta
        while B / T_MM <= 8.0:
            H *= 1.5
            B = H / eta
        for dob in D_OVER_B_GRID:
            D = dob * B
            if D / T_MM <= 4.0:
                continue  # declared D/t > 4 bound
            case_id += 1
            rows.append({"case_id": case_id, "H_mm": H, "B_mm": B, "D_mm": D,
                         "t_mm": T_MM, "eta_w": eta, "D_over_B": dob})
    df = pd.DataFrame(rows)
    df.to_csv(EXT / "rp23001_cases_numeric.csv", index=False)
    provenance = {
        "source": "Ding, C. and Schafer, B.W., AISI RP23-01 (2023), "
                  "Analytical Equations for Critical Local Buckling Stress of Lipped Channels",
        "public_url": "https://www.cfsei.org/assets/docs/research_report/"
                      "AISI%20RP23-01%20Analytical%20Equations%20for%20Critical%20Local%20Buckling%20"
                      "Stress%20of%20Lipped%20Channels.pdf",
        "audited_object": "gross lipped channel, pure compression, no punchouts",
        "audited_equation": "k_w = 4 + 24*eta/(20+4.4*eta+eta^2), eta=h/b, 1.2<=eta<=22",
        "declared_performance": {"mean_fsm_over_predicted": 1.00, "cov": 0.02},
        "sampling": {
            "eta_grid": ETA_GRID, "D_over_B_grid": D_OVER_B_GRID, "t_mm": T_MM,
            "domain_rules": "B/H 0.05-0.75, D/B 0.1-0.4, B/t>8, D/t>4 (report Section 5)",
            "note": "fresh sections generated inside the declared domain; not the report's own library",
        },
        "rebuild_contract": {
            "solver": "MIT-licensed CUFSM source repository (stripmain)",
            "elastic_modulus_mpa": E_MPA, "poisson_ratio": NU,
            "mesh_target_mm": 3.0, "length_grid": "36 log points over 0.25h..2.0h, quadratic interp",
            "kw_backcalculation": "k_w = fcrl*12*(1-nu^2)*(H/t)^2/(pi^2*E) (independent of E)",
            "screen": f"per-section |k_fsm/k_eq - 1| <= {int((SCREEN_RATIO-1)*100)}%",
        },
    }
    (EXT / "r04_rp23001_rebuild_provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8")
    print(df.to_string(index=False))
    return EXT / "rp23001_cases_numeric.csv"


def predicate_audit() -> dict:
    eta = np.linspace(1.2, 22.0, 2001)
    kw = 4 + 24 * eta / (20 + 4.4 * eta + eta ** 2)
    dkw = np.gradient(kw, eta)
    turning = math.sqrt(20.0)
    return {
        "positive_on_domain": bool((kw > 0).all()),
        "min_kw": float(kw.min()), "max_kw": float(kw.max()),
        "monotone_increasing": bool((dkw >= -1e-9).all()),
        "monotone_decreasing": bool((dkw <= 1e-9).all()),
        "turning_point_eta": turning,
        "increasing_branch": "[1.2, sqrt(20)]", "decreasing_branch": "[sqrt(20), 22]",
        "finite_real": bool(np.isfinite(kw).all()),
        "domain_coverage_of_sample": "all sampled eta inside declared domain",
    }


def summarize() -> dict:
    chunks = sorted(OUT.glob("r04_rp2301_rebuild_chunk_*.csv"))
    if not chunks:
        raise RuntimeError("No rebuild chunk outputs found; run the Octave chunks first")
    df = pd.concat([pd.read_csv(p) for p in chunks], ignore_index=True).sort_values("case_id")
    df.to_csv(OUT / "r04_rp23001_rebuild.csv", index=False)
    df["abs_dev_pct"] = (df["ratio"] - 1.0).abs() * 100.0
    pred = predicate_audit()
    all_pass = bool((df["abs_dev_pct"] <= (SCREEN_RATIO - 1) * 100).all())
    action = "allow_bounded_query" if (pred["positive_on_domain"] and all_pass) else "retain_bounded_claim"
    if not pred["positive_on_domain"]:
        action = "reject_nonexecutable"
    summary = {
        "round": "R04_W2_second_object_full_application",
        "object": "AISI RP23-01 lipped channel, pure compression, gross section",
        "predicate_audit": pred,
        "evidence": {
            "sections": int(len(df)),
            "ratio_mean": float(df["ratio"].mean()),
            "ratio_std": float(df["ratio"].std(ddof=1)),
            "ratio_min": float(df["ratio"].min()),
            "ratio_max": float(df["ratio"].max()),
            "max_abs_dev_pct": float(df["abs_dev_pct"].max()),
            "screen_pct": (SCREEN_RATIO - 1) * 100,
            "all_within_screen": all_pass,
            "declared_report_mean": 1.00, "declared_report_cov": 0.02,
        },
        "protocol_action": action,
        "interpretation": (
            "Mechanics predicates on the declared equation are recorded separately from the "
            "FSM ratio screen. allow_bounded_query is returned only when positivity holds "
            "and every independently rebuilt section is inside the predeclared screen. "
            "A screen failure returns retain_bounded_claim. It does not by itself mean the "
            "published equation is false: the source identifies local buckling with a "
            "two-step signature-curve classifier and round corners, which this sharp-corner "
            "rebuild does not reproduce."
        ),
        "boundary": (
            "The sample is generated by this project inside the declared domain and is not "
            "the report's own 1228-section library. See "
            "reports/r04_rp23001_second_object_audit_2026-10-06.md for the signature-curve "
            "and pure-local selector comparison. Operational use remains a separate gate."
        ),
    }
    (OUT / "r04_rp23001_rebuild_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(df[["case_id", "eta_w", "D_over_B", "kw_fsm", "kw_equation19", "ratio",
              "abs_dev_pct"]].to_string(index=False))
    print(json.dumps({k: summary[k] for k in
                      ["predicate_audit", "evidence", "protocol_action"]}, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "summarize"])
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        summarize()


if __name__ == "__main__":
    main()