"""R04 W2 — Combine the RP23-01 selector runs into one auditable summary.

Reads only CSV outputs already produced by the Octave rebuilds. Does not refit
the screen. The predeclared screen remains |k_fsm/k_eq - 1| <= 10% per section.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SCREEN = 10.0


def _stats(series: pd.Series) -> dict:
    dev = (series - 1.0).abs() * 100.0
    return {
        "n": int(series.shape[0]),
        "ratio_mean": float(series.mean()),
        "ratio_min": float(series.min()),
        "ratio_max": float(series.max()),
        "max_abs_dev_pct": float(dev.max()),
        "n_within_5pct": int((dev <= 5.0).sum()),
        "n_within_10pct": int((dev <= SCREEN).sum()),
        "n_outside_10pct": int((dev > SCREEN).sum()),
    }


def main() -> None:
    sig = pd.read_csv(OUT / "r04_rp2301_first_minimum.csv")
    loc_paths = sorted(OUT.glob("r04_rp2301_local_mode_chunk_*.csv"))
    loc = pd.concat([pd.read_csv(p) for p in loc_paths], ignore_index=True) if loc_paths else pd.DataFrame()
    sig_stats = _stats(sig["ratio_first"])
    failing = sig.loc[(sig["ratio_first"] - 1.0).abs() * 100.0 > SCREEN,
                      ["case_id", "eta_w", "D_over_B", "ratio_first", "L_over_H_first", "n_minima"]]
    summary = {
        "round": "R04_W2_second_object",
        "object": "AISI RP23-01 Eq. 19, gross lipped channel, pure compression",
        "equation": "k_w = 4 + 24*eta/(20 + 4.4*eta + eta^2), eta=h/b, 1.2<=eta<=22",
        "sample": "15 sharp-corner centreline sections generated inside the declared ratio domain; not the report's 1228-section library",
        "predeclared_screen_pct": SCREEN,
        "predicate_audit": {
            "positive_on_declared_domain": True,
            "finite_on_declared_domain": True,
            "global_monotonicity": False,
            "turning_point_eta": 20 ** 0.5,
            "note": "Global increasing is inapplicable. The derivative changes sign at eta=sqrt(20).",
        },
        "signature_curve_minimum": {
            **sig_stats,
            "n_sections_with_two_or_more_minima_in_0.2h_to_3h": int((sig["n_minima"] >= 2).sum()),
            "selector": "lowest eigenvalue; identical here to the first interior minimum because every curve had one minimum",
            "outside_screen": failing.to_dict(orient="records"),
        },
        "pure_local_cFSM": {
            "sections": "cases 11-15 only (eta=8, 12, 16, 20); chunks 1-2 were not run after this selector proved to be a different quantity from the report",
            "stats": _stats(loc["ratio_local"]) if len(loc) else None,
            "note": "GBTcon.local=1 and global/distortional/other=0. This constrained eigenvalue is higher than the signature-curve minimum. It is not the report's two-step classifier.",
        },
        "protocol_action": "retain_bounded_claim",
        "why_not_allow_bounded_query": (
            "Three of 15 signature-curve sections exceed the predeclared 10% screen "
            "(all at eta>=12). The pure-local constraint on those same high-eta sections "
            "moves the ratio the other way, up to about +33%. The audit outcome depends "
            "on the mode selector. The source uses round corners and a two-step local/"
            "distortional classifier that this rebuild does not reproduce, so the screen "
            "failure is not reported as an error in Eq. 19."
        ),
        "open_model_gaps": [
            "round corners with at least four elements per corner, as stated in RP23-01 Section 3",
            "the report's two-step signature-curve classifier (Li and Schafer 2010), as distinct from a pure-local constrained eigenvalue",
            "the report's own 1228-section library in Appendix A, which is not redistributed here as a recomputed table",
        ],
    }
    (OUT / "r04_rp23001_selector_audit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "signature": sig_stats,
        "n_multi_minima": summary["signature_curve_minimum"]["n_sections_with_two_or_more_minima_in_0.2h_to_3h"],
        "local": summary["pure_local_cFSM"]["stats"],
        "action": summary["protocol_action"],
    }, indent=2))


if __name__ == "__main__":
    main()
