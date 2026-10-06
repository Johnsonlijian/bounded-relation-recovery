"""Action reduction for the BRR protocol.

The output action is the single highest permitted level whose upstream predicates all
pass; open gates are recorded, never silently cleared. `allow_operational_use` can never
be granted by this function because its extra gates (independent source-model rerun and
human engineering sign-off) are not computable inputs.
"""

from __future__ import annotations

from .schema import Action, ActionLevel, BoundedRelationRun, PredicateType

REJECTING_TYPES = {
    PredicateType.MECHANICS_POSITIVITY,
    PredicateType.MECHANICS_FINITENESS,
    PredicateType.PROVENANCE_SOURCE_VERIFIED,
}
RETAINING_TYPES = {
    PredicateType.MECHANICS_MONOTONICITY,
    PredicateType.EVIDENCE_INTERVAL_FEASIBILITY,
    PredicateType.EVIDENCE_COVERAGE,
}


def reduce_action(run: BoundedRelationRun) -> Action:
    failed = [p.predicate_type for p in run.predicates if p.result is False]
    open_gates = [p.predicate_id for p in run.predicates if p.result is None]

    if any(t in REJECTING_TYPES for t in failed):
        return Action(action_id=f"{run.run_id}:reject", level=ActionLevel.REJECT_NONEXECUTABLE,
                      scope="route non-executable under mechanics/provenance predicates",
                      open_gates=open_gates)

    if failed or open_gates:
        return Action(action_id=f"{run.run_id}:retain", level=ActionLevel.RETAIN_BOUNDED_CLAIM,
                      scope="claim retained within the tested evidence scope",
                      open_gates=open_gates + [str(t) for t in failed])

    return Action(action_id=f"{run.run_id}:query", level=ActionLevel.ALLOW_BOUNDED_QUERY,
                  scope="bounded query permitted within the tested object/evidence scope",
                  open_gates=["operational_use_gates: independent_source_model_rerun, "
                              "human_engineering_signoff"])