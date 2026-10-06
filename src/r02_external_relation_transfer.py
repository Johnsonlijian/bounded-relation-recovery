from __future__ import annotations

"""R02 source-anchored transfer card for a second relation and predicate map.

This is a relation/predicate transfer check, not a second recovery of a
published finite-strip data set.  The AISI RP23-01 equation is evaluated from
the public report, rounded to the declared precision, and checked under an
explicit positive-and-bounded predicate map.  The report's original FSM data
are not redistributed or rerun here.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
EXTERNAL = ROOT / "external_sources"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

SOURCE_URL = (
    "https://www.buildusingsteel.org/wp-content/uploads/2023/07/"
    "AISI-RP23-01-Analytical-Equations-for-Critical-Local-Buckling-Stress-"
    "of-Lipped-Channels-second-printing.pdf"
)
SOURCE_FILE = EXTERNAL / "aisi_rp23_01_2023.pdf"
DISPLAY_HALF_WIDTH = 0.005
DOMAIN = (1.2, 22.0)
TURNING_POINT = float(np.sqrt(20.0))


def aisi_kw(eta):
    eta = np.asarray(eta, dtype=float)
    return 4.0 + 24.0 * eta / (20.0 + 4.4 * eta + eta**2)


def aisi_dkw(eta):
    eta = np.asarray(eta, dtype=float)
    denominator = 20.0 + 4.4 * eta + eta**2
    return 24.0 * (20.0 - eta**2) / denominator**2


def main():
    grid = np.linspace(DOMAIN[0], DOMAIN[1], 1001)
    values = aisi_kw(grid)
    derivative = aisi_dkw(grid)
    sample_eta = np.array([1.2, 2.0, 4.0, TURNING_POINT, 6.0, 10.0, 22.0])
    exact = aisi_kw(sample_eta)
    rounded = np.round(exact, 2)
    interval_low = rounded - DISPLAY_HALF_WIDTH
    interval_high = rounded + DISPLAY_HALF_WIDTH
    rows = pd.DataFrame(
        {
            "eta_h_over_b": sample_eta,
            "exact_k_w": exact,
            "reported_k_w_2dp": rounded,
            "interval_low": interval_low,
            "interval_high": interval_high,
            "exact_inside_rounding_interval": (exact >= interval_low) & (exact <= interval_high),
            "derivative": aisi_dkw(sample_eta),
        }
    )
    rows.to_csv(OUT / "r02_external_relation_transfer.csv", index=False)

    source_sha256 = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest() if SOURCE_FILE.exists() else None
    summary = {
        "evidence_class": "independent_public_relation_transfer_card",
        "source_url": SOURCE_URL,
        "source_file": str(SOURCE_FILE.relative_to(ROOT)),
        "source_file_sha256": source_sha256,
        "source_report_printed_page": 12,
        "source_pdf_page": 14,
        "source_equation": "k_w = 4 + 24 eta/(20 + 4.4 eta + eta^2), eta=h/b, 1.2 <= eta <= 22",
        "object": "lipped channel under pure compression",
        "domain": list(DOMAIN),
        "sample_cells": int(len(rows)),
        "rounding_half_width": DISPLAY_HALF_WIDTH,
        "rounding_interval_gate": bool(rows["exact_inside_rounding_interval"].all()),
        "positive_domain_gate": bool(np.all(values > 0)),
        "finite_domain_gate": bool(np.isfinite(values).all()),
        "global_increasing_predicate": "not satisfied",
        "piecewise_monotonicity": {
            "turning_point_eta": TURNING_POINT,
            "increasing_interval": [DOMAIN[0], TURNING_POINT],
            "decreasing_interval": [TURNING_POINT, DOMAIN[1]],
        },
        "bounded_predicate_action": "allow_bounded_query",
        "global_increasing_required_action": "reject_nonexecutable",
        "sign_flipped_positive_predicate_action": "reject_nonexecutable",
        "source_fsm_rerun": False,
        "boundary": "source equation and rounded card only; the report's 1228-section FSM study is not rerun and this card does not recover a new relation",
    }
    (OUT / "r02_external_relation_transfer_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 6.2), sharex=True, constrained_layout=True)
    axes[0].plot(grid, values, color="#2166AC", lw=2.4, label=r"AISI RP23-01 $k_w(\eta)$")
    axes[0].scatter(sample_eta, rounded, color="#E76F51", s=22, zorder=3, label="rounded source card")
    axes[0].axvline(TURNING_POINT, color="#455A64", ls="--", lw=1.1, label=r"turning point $\sqrt{20}$")
    axes[0].set_ylabel(r"Buckling coefficient $k_w$")
    axes[0].set_title("External relation transfer card: bounded but non-monotonic")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", color="#ECEFF1")
    axes[1].plot(grid, derivative, color="#2A9D8F", lw=2.1)
    axes[1].axhline(0, color="#263238", lw=1.0)
    axes[1].axvline(TURNING_POINT, color="#455A64", ls="--", lw=1.1)
    axes[1].set_xlabel(r"Geometry ratio $\eta=h/b$")
    axes[1].set_ylabel(r"$dk_w/d\eta$")
    axes[1].grid(axis="y", color="#ECEFF1")
    for ext, kwargs in [("svg", {}), ("png", {"dpi": 300}), ("pdf", {})]:
        fig.savefig(FIG / f"figure7_external_relation_transfer.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
