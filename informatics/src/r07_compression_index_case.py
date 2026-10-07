from __future__ import annotations

"""Execute the independent geotechnical BRR case through the shared action reducer.

Source: Uzer (2024), Buildings 14(9), 2688, DOI 10.3390/buildings14092688.
The printed Appendix B Table A2 is the independent oedometer response table; the
nine e0-only correlations are attributed published candidates from the same source.
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brr.evaluate import run_scalar_correlation_protocol  # noqa: E402

PDF = ROOT / "external_sources" / "second_domain" / "buildings-14-02688.pdf"
OUT = ROOT / "outputs"
DATA = ROOT / "data"
OUT.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
DISPLAY_HALF_UNIT = 0.0005

CORRELATIONS = [
    ("Peck & Reed (1954)", "0.208 e0 + 0.0083", lambda e: 0.208 * e + 0.0083),
    ("Sowers & Sowers (1970)", "0.75 (e0 - 0.50)", lambda e: 0.75 * (e - 0.50)),
    ("Azzouz et al. (1976) a", "0.40 (e0 - 0.25)", lambda e: 0.40 * (e - 0.25)),
    ("Rendon-Herrero (1980)", "0.49 e0 - 0.11", lambda e: 0.49 * e - 0.11),
    ("Park & Lee (2011)", "0.287 e0 - 0.015", lambda e: 0.287 * e - 0.015),
    ("Ahadiyan et al. (2008)", "1.02 - 0.95 e0", lambda e: 1.02 - 0.95 * e),
    ("Gunduz & Arman (2007)", "0.506 e0 - 0.11", lambda e: 0.506 * e - 0.11),
    ("Bowles (1989)", "0.40 e0 - 0.10", lambda e: 0.40 * e - 0.10),
    ("Lav & Ansal (2001)", "0.407 e0 - 0.094", lambda e: 0.407 * e - 0.094),
]


def parse_dataset() -> list[tuple[float, float]]:
    import pypdf
    r = pypdf.PdfReader(str(PDF))
    rows: list[tuple[float, float]] = []
    for pg in range(14, 19):
        text = r.pages[pg - 1].extract_text() or ""
        nums = [float(x) for x in re.findall(r"(?<![\d.])(\d{1,4}\.\d{1,4})(?![\d])", text)]
        for i in range(0, len(nums) - 5, 6):
            wn, ll, pl, pi, e0, cc = nums[i:i + 6]
            if not (0.05 <= wn <= 2.5 and 0.15 <= ll <= 1.8 and 0.05 <= pl <= 1.2
                    and 0.0 <= pi <= 1.2 and 0.45 <= e0 <= 2.6 and 0.03 <= cc <= 1.2):
                continue
            if abs((ll - pl) - pi) > 0.02:
                continue
            rows.append((e0, cc))
    seen: set[tuple[float, float]] = set()
    unique: list[tuple[float, float]] = []
    for row in rows:
        if row not in seen:
            seen.add(row)
            unique.append(row)
    return unique


def main() -> None:
    data = parse_dataset()
    print(f"parsed dataset rows: {len(data)} (paper states 458 x 6)")
    if len(data) < 100:
        raise SystemExit("PARSE FAILED - refusing to continue")
    states = [e for e, _ in data]
    observed = [c for _, c in data]
    domain = (min(states), max(states))
    print(f"declared observed-table domain e0={domain[0]:.3f} .. {domain[1]:.3f}")

    results = []
    runs = []
    for name, form, fn in CORRELATIONS:
        run = run_scalar_correlation_protocol(
            fn, "geotech_correlation", name, states, observed, domain, DISPLAY_HALF_UNIT,
        )
        runs.append(run)
        pred = [fn(e) for e in states]
        dev = [abs(p - o) for p, o in zip(pred, observed)]
        predicate_results = {p.predicate_id: p.result for p in run.predicates}
        results.append({
            "relation": name,
            "form": form,
            "positive_on_domain": predicate_results["P1.positivity"],
            "increasing": predicate_results["P2.monotonicity"],
            "finite": predicate_results["P3.finiteness"],
            "max_abs_dev": max(dev),
            "mean_abs_dev": sum(dev) / len(dev),
            "rmse": (sum(d * d for d in dev) / len(dev)) ** 0.5,
            "within_displayed_half_unit": sum(d <= DISPLAY_HALF_UNIT for d in dev),
            "cells": len(dev),
            "fraction_within": sum(d <= DISPLAY_HALF_UNIT for d in dev) / len(dev),
            "median_ratio_pred_obs": sorted(p / o for p, o in zip(pred, observed) if o > 0)[len(dev) // 2],
            "action": run.action.level.name,
            "action_scope": run.action.scope,
            "predicate_results": predicate_results,
        })

    results.sort(key=lambda r: r["rmse"])
    print("\nrelation                     pos inc fin  RMSE      max|d|   within/445                 action")
    for r in results:
        print(f"{r['relation']:<26} {int(r['positive_on_domain'])}   {int(r['increasing'])}   "
              f"{int(r['finite'])}   {r['rmse']:.4f}   {r['max_abs_dev']:.4f}   "
              f"{r['within_displayed_half_unit']:>4}/{r['cells']}   {r['action']}")

    action_counts = {}
    for r in results:
        action_counts[r["action"]] = action_counts.get(r["action"], 0) + 1
    payload = {
        "case": "geotechnical_compression_index",
        "source": {
            "citation": "Uzer, A.U. (2024). Accurate Prediction of Compression Index of Normally Consolidated Soils Using Artificial Neural Networks. Buildings 14(9), 2688.",
            "doi": "10.3390/buildings14092688",
            "license": "CC-BY",
            "pdf_sha256": "cf15bfdbe9b91e2145e39d000305f781d9b1ead1280d9001f2f4a0959939e2af",
            "closed_form_locator": "p.13, table of attributed empirical Cc correlations",
            "evidence_locator": "Appendix B, Table A2, pp.14-17",
        },
        "contract": {
            "object": "normally consolidated fine-grained soil (oedometer records)",
            "state": "initial void ratio e0",
            "declared_domain": list(domain),
            "response": "compression index Cc",
            "displayed_half_unit": DISPLAY_HALF_UNIT,
            "candidate_class": "published e0-only Cc correlations (not a permutation class)",
            "cells_parsed": len(data),
            "reducer": "src/brr/actions.py::reduce_action",
            "interval_predicate": "direct response interval; no positive scale or solver selector required",
        },
        "action_summary": action_counts,
        "results": results,
        "runs": [
            {
                "run_id": run.run_id,
                "action": run.action.level.name,
                "predicates": {p.predicate_id: {"result": p.result, "note": p.note} for p in run.predicates},
                "source": run.provenance[0].locator,
            }
            for run in runs
        ],
        "boundary": "The parsed cells are a machine transcription of the printed table and were screened for physical admissibility; they are not the authors' original spreadsheet. The observed table range is the declared domain because the source does not publish a wider domain for this e0-only comparison. The dataset is independent of the listed correlations.",
    }
    (OUT / "r07_compression_index_contract.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    csv_text = "e0,Cc\n" + "".join(f"{e},{c}\n" for e, c in data)
    (OUT / "r07_compression_index_dataset.csv").write_text(csv_text, encoding="utf-8")
    (DATA / "r07_compression_index_dataset.csv").write_text(csv_text, encoding="utf-8")
    print(f"action summary: {action_counts}")
    print(f"wrote {OUT / 'r07_compression_index_contract.json'}")
    print(f"wrote {OUT / 'r07_compression_index_dataset.csv'}")
    print(f"wrote {DATA / 'r07_compression_index_dataset.csv'}")


if __name__ == "__main__":
    main()
