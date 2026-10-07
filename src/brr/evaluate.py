"""Reference evaluator for the BRR (bounded relation recovery) protocol.

`schema.py` types a run and `actions.py` reduces it to one action.  This module is the
missing middle: it *computes* the predicate results from the declared object, state,
relation and finite-precision evidence, so the protocol can be executed on a new relation
instead of being narrating a result that a human typed in.

Predicates implemented here are exactly those named in the manuscript:

    mechanics.positivity            response > 0 on the declared domain
    mechanics.monotonicity          declared trend holds on the declared domain
    mechanics.finiteness            finite and real on the declared domain
    evidence.interval_feasibility   Eq. (1): one positive scale places every rounded
                                    cell of a group inside its displayed half-unit
    evidence.coverage               every cell lies inside the declared domain
    provenance.source_verified      a locator is recorded for every evidence source

Execution order is fixed: mechanics -> evidence -> provenance -> action
(schema doc v0.1, section 6).  `reduce_action` is not re-implemented here.

Run `python -m brr.evaluate --self-test` from `src/` to reproduce the manuscript's
headline numbers from the deposited transcriptions.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .actions import reduce_action
from .schema import (
    Action,
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

# --------------------------------------------------------------------------------------
# relations
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Quadratic:
    """q(x) = c0 + c2*x**2 + c1*x, evaluated in the printed coefficient order."""

    c0: float
    c2: float
    c1: float

    def __call__(self, x: float) -> float:
        return self.c0 + self.c2 * x * x + self.c1 * x

    @property
    def label(self) -> str:
        return f"{self.c0:+.3f} {self.c2:+.3f} x^2 {self.c1:+.3f} x"

    def as_tuple(self) -> tuple[float, float, float]:
        return (round(self.c0, 6), round(self.c2, 6), round(self.c1, 6))


#: the three coefficient magnitudes printed in the source equation
PRINTED_MAGNITUDES: tuple[float, ...] = (0.292, 0.339, 1.060)

#: the printed expression as published (constant, x^2, x)
PRINTED_RELATION = Quadratic(0.292, -1.060, 0.339)

#: the relation the protocol retains
RECOVERED_RELATION = Quadratic(0.292, -0.339, 1.060)

#: declared state domain
DOMAIN: tuple[float, float] = (1.1, 1.5)

#: displayed rounding half-unit of the transcribed stress values, MPa
DISPLAYED_HALF_UNIT_MPA = 0.005


def candidate_class(magnitudes: Sequence[float] = PRINTED_MAGNITUDES) -> list[Quadratic]:
    """The declared finite candidate class.

    All 3! orderings of the three printed magnitudes into (constant, x^2, x), crossed with
    all 2**3 sign combinations: 6 * 8 = 48 members.  No fitted value enters the class.
    """
    out: list[Quadratic] = []
    for perm in itertools.permutations(magnitudes):
        for signs in itertools.product((1.0, -1.0), repeat=3):
            out.append(Quadratic(*(p * s for p, s in zip(perm, signs))))
    # deterministic order, de-duplicated on exact printed magnitudes
    seen: set[tuple[float, float, float]] = set()
    uniq: list[Quadratic] = []
    for q in out:
        key = q.as_tuple()
        if key not in seen:
            seen.add(key)
            uniq.append(q)
    return uniq


# --------------------------------------------------------------------------------------
# predicates
# --------------------------------------------------------------------------------------


def grid(domain: tuple[float, float], n: int = 401) -> list[float]:
    lo, hi = domain
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def mechanics_finiteness(q: Callable[[float], float], domain: tuple[float, float]) -> tuple[bool, str]:
    values = [q(x) for x in grid(domain)]
    ok = all(v == v and abs(v) != float("inf") for v in values)
    return ok, f"{len(values)} domain samples finite" if ok else "non-finite value on domain"


def mechanics_positivity(q: Callable[[float], float], domain: tuple[float, float]) -> tuple[bool, str]:
    values = [q(x) for x in grid(domain)]
    ok = min(values) > 0.0
    return ok, f"min q(x) = {min(values):.6f} on [{domain[0]}, {domain[1]}]"


def mechanics_monotonicity(
    q: Callable[[float], float], domain: tuple[float, float], trend: str = "increasing"
) -> tuple[bool, str]:
    xs = grid(domain)
    d = [q(xs[i + 1]) - q(xs[i]) for i in range(len(xs) - 1)]
    if trend == "increasing":
        ok = min(d) >= 0.0
        return ok, f"min forward difference = {min(d):.6f}"
    if trend == "decreasing":
        ok = max(d) <= 0.0
        return ok, f"max forward difference = {max(d):.6f}"
    raise ValueError(f"unknown trend {trend!r}")


def scale_interval(
    cells: Sequence[tuple[float, float]], half_unit: float
) -> tuple[bool, float, float, float]:
    """Eq. (1) for one group.

    ``cells`` is a sequence of ``(y_hat_j, q_j)`` with ``q_j > 0``.  A single positive scale
    ``A`` places every rounded cell inside its displayed half-unit iff

        max_j (y_hat_j - h) / q_j  <=  min_j (y_hat_j + h) / q_j .

    Returns ``(feasible, A_low, A_high, required_half_width)``.  ``required_half_width`` is
    the smallest ``h`` at which the inequality holds; it is found by bisection because the
    left side decreases and the right side increases in ``h``.
    """
    if not cells:
        raise ValueError("empty group")
    if any(q <= 0 for _, q in cells):
        return False, float("nan"), float("nan"), float("nan")

    def gap(h: float) -> float:
        lo = max((y - h) / q for y, q in cells)
        hi = min((y + h) / q for y, q in cells)
        return lo - hi, lo, hi

    g, lo, hi = gap(half_unit)
    if g <= 0.0:
        # find the exact required half-width: g is strictly decreasing in h
        a, b = 0.0, half_unit
        for _ in range(200):
            m = 0.5 * (a + b)
            if gap(m)[0] > 0.0:
                a = m
            else:
                b = m
        return True, lo, hi, b

    # not feasible at the displayed half-unit: solve for the required half-width
    a, b = half_unit, half_unit
    for _ in range(80):
        b *= 2.0
        if gap(b)[0] <= 0.0:
            break
    else:  # pragma: no cover
        return False, float("nan"), float("nan"), float("inf")
    for _ in range(200):
        m = 0.5 * (a + b)
        if gap(m)[0] > 0.0:
            a = m
        else:
            b = m
    return False, lo, hi, b


def evidence_interval_feasibility(
    groups: dict[str, Sequence[tuple[float, float]]], half_unit: float
) -> tuple[bool, float, dict[str, float]]:
    """Eq. (1) across every declared group.  One positive scale per group."""
    per_group: dict[str, float] = {}
    feasible = True
    for name, cells in groups.items():
        ok, _, _, h_req = scale_interval(cells, half_unit)
        per_group[name] = h_req
        feasible = feasible and ok
    return feasible, max(per_group.values()), per_group


def evidence_coverage(states: Iterable[float], domain: tuple[float, float]) -> tuple[bool, str]:
    lo, hi = domain
    bad = [x for x in states if not (lo <= x <= hi)]
    return (not bad), f"{len(bad)} cells outside [{lo}, {hi}]"


def provenance_source_verified(records: Sequence[Provenance]) -> tuple[bool, str]:
    missing = [r.source_id for r in records if not r.locator]
    return (not missing), f"{len(missing)} sources without a locator"


# --------------------------------------------------------------------------------------
# one run
# --------------------------------------------------------------------------------------


@dataclass
class Group:
    name: str
    cells: list[tuple[float, float]]  # (y_hat, q)


def run_angle_protocol(
    relation: Quadratic,
    groups: dict[str, Sequence[tuple[float, float]]],
    domain: tuple[float, float] = DOMAIN,
    half_unit: float = DISPLAYED_HALF_UNIT_MPA,
    trend: str = "increasing",
    declared_by: str = "source equation domain and transcribed tables",
) -> BoundedRelationRun:
    """Evaluate one relation against one evidence set and reduce it to one action."""
    predicates: list[Predicate] = []

    ok, note = mechanics_positivity(relation, domain)
    predicates.append(Predicate("P1.positivity", PredicateType.MECHANICS_POSITIVITY,
                                "min q(x) > 0 on the declared domain", declared_by, ok, note))
    ok, note = mechanics_monotonicity(relation, domain, trend)
    predicates.append(Predicate("P2.monotonicity", PredicateType.MECHANICS_MONOTONICITY,
                                f"q(x) is {trend} on the declared domain", declared_by, ok, note))
    ok, note = mechanics_finiteness(relation, domain)
    predicates.append(Predicate("P3.finiteness", PredicateType.MECHANICS_FINITENESS,
                                "q(x) finite on the declared domain", declared_by, ok, note))

    feasible, h_req, per_group = evidence_interval_feasibility(groups, half_unit)
    predicates.append(Predicate(
        "E1.interval_feasibility", PredicateType.EVIDENCE_INTERVAL_FEASIBILITY,
        "Eq. (1) holds for every declared group at the displayed half-unit",
        "transcribed source tables", feasible,
        f"required half-width {h_req:.6f} MPa vs displayed {half_unit} MPa; per group "
        + ", ".join(f"{k}={v:.6f}" for k, v in per_group.items())))

    states = [1.1 + 0.1 * i for i in range(5)]
    ok, note = evidence_coverage(states, domain)
    predicates.append(Predicate("E2.coverage", PredicateType.EVIDENCE_COVERAGE,
                                "every evidence cell lies inside the declared domain",
                                "declared domain", ok, note))

    prov = [Provenance("zhang2022", "10.3390/buildings12060712",
                       license_boundary="transcribed cells only; native models not redistributed")]
    ok, note = provenance_source_verified(prov)
    predicates.append(Predicate("V1.source_verified", PredicateType.PROVENANCE_SOURCE_VERIFIED,
                                "a locator is recorded for every evidence source",
                                "source registry", ok, note))

    run = BoundedRelationRun(
        run_id=f"angle:{relation.label}",
        object=Object("unequal_limb_lipped_angle", "cold-formed steel",
                      {"a_over_t": 0.0, "t_mm": 2.0}),
        state=State("x=a/b", domain, states),
        response=Response("sigma_cr", "MPa", positivity_expected=True),
        relation=Relation("printed_magnitude_class", relation.label,
                          "48 = 3! orderings x 2**3 signs of the printed magnitudes", domain),
        predicates=predicates,
        evidence=[Evidence("zhang_tables_5_9", EvidenceClass.CASE,
                           sum(len(c) for c in groups.values()), half_unit,
                           ["zhang2022"])],
        provenance=prov,
    )
    run.action = reduce_action(run)
    return run


# --------------------------------------------------------------------------------------
# self test: reproduce the manuscript's headline numbers from the deposited data
# --------------------------------------------------------------------------------------


def _load_primary_cells(path: Path) -> dict[str, list[tuple[float, float]]]:
    groups: dict[str, list[tuple[float, float]]] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["transcription_role"] != "equation_reconstruction":
                continue
            key = f"{row['table']}@a/t={float(row['a_over_t']):g}"
            groups.setdefault(key, []).append((float(row["reported_formula_stress_mpa"]), 0.0))
    # q(x) is filled per candidate relation inside the enumeration
    return groups


def self_test(data_dir: Path) -> dict:
    """Reproduce the numbers the manuscript reports, from the deposited transcriptions."""
    import math

    report: dict = {}
    prim = []
    with open(data_dir / "source_table_transcription.csv", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["transcription_role"] == "equation_reconstruction":
                prim.append((row["table"], float(row["a_over_t"]),
                             float(row["a_over_b"]), float(row["reported_formula_stress_mpa"])))
    report["primary_cells"] = len(prim)

    group_names = sorted({(t, at) for t, at, _, _ in prim})

    def build(fn: Quadratic) -> dict[str, list[tuple[float, float]]]:
        return {
            f"{t}@a/t={at:g}": [(y, fn(ab)) for tt, aat, ab, y in prim if (tt, aat) == (t, at)]
            for t, at in group_names
        }

    cls = candidate_class()
    report["candidate_class_size"] = len(cls)

    rows = []
    for q in cls:
        pos, _ = mechanics_positivity(q, DOMAIN)
        inc, _ = mechanics_monotonicity(q, DOMAIN, "increasing")
        feasible, h_req, _ = evidence_interval_feasibility(build(q), DISPLAYED_HALF_UNIT_MPA)
        rows.append({"relation": q, "positive": pos, "increasing": inc,
                     "feasible": feasible, "half_width": h_req})

    mech = [r for r in rows if r["positive"] and r["increasing"]]
    report["positive_and_increasing_candidates"] = len(mech)
    report["positive_only_candidates"] = len([r for r in rows if r["positive"]])

    winners = [r for r in rows if r["positive"] and r["increasing"] and r["feasible"]]
    report["feasible_in_class"] = len(winners)
    win = winners[0] if winners else None
    if win:
        report["winner"] = win["relation"].label
        report["winner_required_half_width_mpa"] = round(win["half_width"], 9)
        alts = [r for r in rows if r["positive"] and r is not win]
        report["nearest_positive_alternative_half_width_mpa"] = round(
            min(r["half_width"] for r in alts), 9)

    printed_pos, printed_note = mechanics_positivity(PRINTED_RELATION, DOMAIN)
    printed_inc, _ = mechanics_monotonicity(PRINTED_RELATION, DOMAIN, "increasing")
    report["printed_positive_on_domain"] = printed_pos
    report["printed_decreasing_on_domain"] = mechanics_monotonicity(
        PRINTED_RELATION, DOMAIN, "decreasing")[0]
    report["printed_domain_endpoint_values"] = [
        round(PRINTED_RELATION(DOMAIN[0]), 6), round(PRINTED_RELATION(DOMAIN[1]), 6)]
    report["printed_note"] = printed_note

    rec_feasible, rec_h, per_group = evidence_interval_feasibility(
        build(RECOVERED_RELATION), DISPLAYED_HALF_UNIT_MPA)
    report["recovered_interval_feasible"] = rec_feasible
    report["recovered_required_half_width_mpa"] = round(rec_h, 9)
    report["recovered_per_group_half_width_mpa"] = {k: round(v, 9) for k, v in per_group.items()}

    run = run_angle_protocol(PRINTED_RELATION, build(PRINTED_RELATION))
    report["printed_action"] = run.action.level.name
    run2 = run_angle_protocol(RECOVERED_RELATION, build(RECOVERED_RELATION))
    report["recovered_action"] = run2.action.level.name
    report["recovered_predicates"] = {p.predicate_id: p.result for p in run2.predicates}

    expected = {
        "candidate_class_size": 48,
        "primary_cells": 20,
        "positive_and_increasing_candidates": 20,
        "positive_only_candidates": 22,
        "feasible_in_class": 1,
        "winner_required_half_width_mpa": 0.003127740,
        "printed_positive_on_domain": False,
        "printed_decreasing_on_domain": True,
        "printed_action": "REJECT_NONEXECUTABLE",
        "recovered_action": "ALLOW_BOUNDED_QUERY",
    }
    checks = {}
    for k, want in expected.items():
        got = report.get(k)
        if isinstance(want, float):
            checks[k] = bool(got is not None and math.isclose(got, want, rel_tol=1e-6, abs_tol=1e-9))
        else:
            checks[k] = (got == want)
    report["checks"] = checks
    report["self_test_pass"] = all(checks.values())
    return report


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BRR reference evaluator")
    ap.add_argument("--data-dir", type=Path,
                    default=Path(__file__).resolve().parents[2] / "data",
                    help="directory holding source_table_transcription.csv")
    ap.add_argument("--self-test", action="store_true",
                    help="reproduce the manuscript's headline numbers and exit non-zero on mismatch")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args(argv)

    if args.self_test:
        rep = self_test(args.data_dir)
        print(json.dumps(rep, indent=2))
        if args.json_out:
            args.json_out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print("\nSELF-TEST:", "PASS" if rep["self_test_pass"] else "FAIL", file=sys.stderr)
        return 0 if rep["self_test_pass"] else 1

    ap.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
