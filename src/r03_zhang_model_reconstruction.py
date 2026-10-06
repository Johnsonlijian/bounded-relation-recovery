from __future__ import annotations

"""Prepare and summarize the independent Zhang et al. CUFSM reconstruction.

The publisher text gives the geometry ratios and rounded stresses but does not
state the elastic modulus used by its MATLAB CUFSM batch.  The reconstruction
therefore freezes a single effective modulus inferred from four predeclared
sentinel rows, then evaluates the remaining published rows without refitting.
It is a bounded source-model recreation, not access to the authors' native
model files.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXT = ROOT / "external_sources" / "zhang_reconstruction"
OUT = ROOT / "outputs"
EXT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

E_EFFECTIVE_MPA = 217400.0
NU = 0.30
THICKNESS_MM = 2.0
MESH_TARGET_MM = 4.0
LENGTH_GRID_POINTS = 32
LENGTH_GRID_FACTOR = (0.30, 1.60)
RELATIVE_TOLERANCE_PCT = 5.0
SENTINEL_CASES = [
    {"table": "Table 4", "a_over_t": 40.0, "a_over_b": 1.1, "c_over_a": 0.20},
    {"table": "Table 4", "a_over_t": 40.0, "a_over_b": 1.1, "c_over_a": 0.50},
    {"table": "Table 8", "a_over_t": 40.0, "a_over_b": 1.1, "c_over_a": 0.20},
    {"table": "Table 8", "a_over_t": 40.0, "a_over_b": 1.1, "c_over_a": 0.50},
]


def prepare() -> Path:
    full = pd.read_csv(DATA / "full_cufsm_cells.csv")
    if len(full) != 630 or set(full["table"]) != {"Table 4", "Table 8"}:
        raise RuntimeError("Expected 630 Table 4/8 rows")
    full = full.copy()
    full.insert(0, "case_id", np.arange(1, len(full) + 1))
    full["is_complex"] = (full["table"] == "Table 8").astype(int)
    numeric = full[["case_id", "is_complex", "a_over_t", "a_over_b", "c_over_a", "cufsm_stress_mpa"]]
    numeric.to_csv(EXT / "zhang_cases_numeric.csv", index=False)
    provenance = {
        "source_article": "Zhang et al. (2022), Buildings 12, 712",
        "doi": "10.3390/buildings12060712",
        "publisher_pdf_url": "https://mdpi-res.com/d_attachment/buildings/buildings-12-00712/article_deploy/buildings-12-00712.pdf",
        "source_tables": ["Table 4", "Table 8"],
        "rows": 630,
        "geometry_scope": "simple and complex lipped unequal-limb angle local-buckling cells; t=2 mm; Table 8 d/c=0.5",
        "solver": "MIT-licensed CUFSM source repository with the local headless stripmain wrapper",
        "solver_repository": "https://github.com/thinwalled/cufsm-git",
        "model_files_from_authors_available": False,
        "reconstruction_contract": {
            "elastic_modulus_mpa": E_EFFECTIVE_MPA,
            "poisson_ratio": NU,
            "thickness_mm": THICKNESS_MM,
            "mesh_target_mm": MESH_TARGET_MM,
            "length_grid_points": LENGTH_GRID_POINTS,
            "length_grid_factor": LENGTH_GRID_FACTOR,
            "mode_selection": "minimum of first positive CUFSM eigenvalue over local-wavelength grid; quadratic interpolation in log wavelength",
            "relative_tolerance_pct": RELATIVE_TOLERANCE_PCT,
            "sentinel_rows_frozen_before_holdout": SENTINEL_CASES,
        },
        "boundary": "E_effective is a metadata-recovery parameter because the article text does not state the batch material modulus; no native author model files are claimed.",
    }
    (EXT / "r03_reconstruction_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return EXT / "zhang_cases_numeric.csv"


def summarize() -> dict:
    chunks = sorted(OUT.glob("r03_zhang_reconstruction_chunk_*.csv"))
    if not chunks:
        raise RuntimeError("No reconstruction chunk outputs found")
    result = pd.concat([pd.read_csv(p) for p in chunks], ignore_index=True).sort_values("case_id")
    if len(result) != 630 or result["case_id"].nunique() != 630:
        raise RuntimeError(f"Expected 630 unique rows, got {len(result)}")
    result.to_csv(OUT / "r03_zhang_model_reconstruction.csv", index=False)
    result["abs_relative_error_pct"] = result["relative_error_pct"].abs()
    table_rows = []
    for table, g in result.groupby("table", sort=True):
        table_rows.append({
            "table": table,
            "rows": int(len(g)),
            "rmse_pct": float(np.sqrt(np.mean(g["relative_error_pct"] ** 2))),
            "mean_bias_pct": float(g["relative_error_pct"].mean()),
            "q95_abs_error_pct": float(np.quantile(g["abs_relative_error_pct"], 0.95)),
            "max_abs_error_pct": float(g["abs_relative_error_pct"].max()),
            "within_5pct_fraction": float((g["abs_relative_error_pct"] <= RELATIVE_TOLERANCE_PCT).mean()),
        })
    by_table = pd.DataFrame(table_rows)
    by_table.to_csv(OUT / "r03_zhang_model_reconstruction_by_table.csv", index=False)
    summary = {
        "source_rows": 630,
        "reconstructed_rows": int(len(result)),
        "duplicate_case_ids": int(result["case_id"].duplicated().sum()),
        "effective_modulus_mpa": E_EFFECTIVE_MPA,
        "poisson_ratio": NU,
        "thickness_mm": THICKNESS_MM,
        "mesh_target_mm": MESH_TARGET_MM,
        "length_grid_points": LENGTH_GRID_POINTS,
        "relative_tolerance_pct": RELATIVE_TOLERANCE_PCT,
        "sentinel_rows": SENTINEL_CASES,
        "overall_rmse_pct": float(np.sqrt(np.mean(result["relative_error_pct"] ** 2))),
        "overall_q95_abs_error_pct": float(np.quantile(result["abs_relative_error_pct"], 0.95)),
        "overall_max_abs_error_pct": float(result["abs_relative_error_pct"].max()),
        "within_tolerance_fraction": float((result["abs_relative_error_pct"] <= RELATIVE_TOLERANCE_PCT).mean()),
        "gate": "pass" if bool((result["abs_relative_error_pct"] <= RELATIVE_TOLERANCE_PCT).all()) else "fail",
        "evidence_class": "bounded_independent_reconstruction_of_published_Zhang_Table4_Table8_cells",
        "model_file_boundary": "native author CUFSM files unavailable; geometry was independently rebuilt from published ratios and E_effective was frozen from four sentinel rows",
        "operational_use": "not allowed; human engineer review and source-model metadata confirmation remain open",
    }
    summary["by_table"] = by_table.to_dict(orient="records")
    (OUT / "r03_zhang_model_reconstruction_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "summarize"])
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare())
    else:
        print(json.dumps(summarize(), indent=2))


if __name__ == "__main__":
    main()
