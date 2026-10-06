from __future__ import annotations

"""Re-run and audit a public CUFSM example as transfer evidence.

The input is a public CUFSM example model/result from the MIT-licensed
thinwalled/cufsm-git repository.  This is deliberately kept separate from the
Zhang et al. lipped-angle evidence: it tests solver reproducibility and the
provenance path, not the source paper's missing model files.
"""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "external_sources" / "cufsm-git"
INPUT = REPO / "examples" / "2006_dsm_design_guide" / "files_and_scripts" / "cnolip_P.mat"
RERUN = ROOT / "external_sources" / "cufsm_public_rerun" / "cnolip_P_rerun.mat"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)


def flatten_curve(curve):
    """Convert a MATLAB cell curve into length x case stress values."""
    cells = np.asarray(curve).reshape(-1)
    values = np.full((len(cells), 10), np.nan)
    lengths = np.full(len(cells), np.nan)
    for i, cell in enumerate(cells):
        arr = np.asarray(cell, dtype=float)
        lengths[i] = arr[0, 0]
        values[i, : min(10, arr.shape[0])] = arr[:10, 1]
    return lengths, values


def main():
    original = loadmat(INPUT, squeeze_me=True, struct_as_record=False)
    rerun = loadmat(RERUN, squeeze_me=True, struct_as_record=False)
    original_curve = np.asarray(original["curve"], dtype=float)
    original_lengths = original_curve[:, 0, 0]
    original_values = original_curve[:, 1, :]
    rerun_lengths, rerun_values = flatten_curve(rerun["curve_rerun"])
    if not np.allclose(original_lengths, rerun_lengths):
        raise RuntimeError("Public CUFSM example length grid changed during rerun")
    diff = rerun_values - original_values
    rel = diff / np.maximum(np.abs(original_values), 1e-12)
    rows = []
    for i, length in enumerate(original_lengths):
        for case in range(original_values.shape[1]):
            rows.append({
                "length": float(length),
                "case": case + 1,
                "source_stress": float(original_values[i, case]),
                "rerun_stress": float(rerun_values[i, case]),
                "absolute_difference": float(diff[i, case]),
                "relative_difference_pct": float(rel[i, case] * 100),
            })
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "r02_cufsm_transfer_curve.csv", index=False)

    # A predeclared numerical reproducibility gate for this public example.
    max_abs = float(np.max(np.abs(diff)))
    max_rel = float(np.max(np.abs(rel)))
    q95_rel = float(np.quantile(np.abs(rel), 0.95))
    summary = {
        "source_repository": "https://github.com/thinwalled/cufsm-git",
        "source_license": "MIT (repository LICENSE)",
        "source_input": str(INPUT.relative_to(ROOT)),
        "rerun_output": str(RERUN.relative_to(ROOT)),
        "source_input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "rerun_output_sha256": hashlib.sha256(RERUN.read_bytes()).hexdigest(),
        "length_count": int(len(original_lengths)),
        "case_count": int(original_values.shape[1]),
        "cell_count": int(original_values.size),
        "max_absolute_difference": max_abs,
        "max_relative_difference_fraction": max_rel,
        "q95_relative_difference_fraction": q95_rel,
        "rmse": float(np.sqrt(np.mean(diff**2))),
        "gate_absolute_tolerance": 1e-3,
        "gate_relative_tolerance_fraction_q95": 0.01,
        "gate": "pass" if max_abs <= 1e-3 and q95_rel <= 0.01 else "fail",
        "evidence_class": "independent_public_CUFSM_example_rerun",
        "boundary": "does not rerun the Zhang et al. lipped-angle source models and does not validate the recovered angle relation",
    }
    (OUT / "r02_cufsm_transfer_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=220)
    for case, color in zip([1, 2, 3], ["#2166AC", "#2A9D8F", "#E76F51"]):
        subset = table[table["case"] == case]
        ax.plot(subset["length"], subset["source_stress"], color=color, lw=2.0, label=f"case {case} source")
        ax.plot(subset["length"], subset["rerun_stress"], color=color, lw=0, marker=".", ms=3, alpha=0.8, label=f"case {case} rerun")
    ax.set_xscale("log")
    ax.set_xlabel("Half-wavelength (public CUFSM grid)")
    ax.set_ylabel("Buckling response (source units)")
    ax.set_title("Independent rerun of a public CUFSM example")
    ax.grid(axis="y", color="#ECEFF1")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    for ext, kwargs in [("svg", {}), ("png", {"dpi": 300}), ("pdf", {})]:
        fig.savefig(FIG / f"figure6_public_cufsm_transfer.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
