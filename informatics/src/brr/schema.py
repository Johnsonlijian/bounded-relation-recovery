"""Typed data model for the BRR protocol (schema v0.1).

Field names are stable inputs to manuscript citations and JSON records; do not rename
without updating knowledge_graph.json and the manuscript method section together.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PredicateType(Enum):
    MECHANICS_POSITIVITY = "mechanics.positivity"
    MECHANICS_MONOTONICITY = "mechanics.monotonicity"
    MECHANICS_FINITENESS = "mechanics.finiteness"
    EVIDENCE_INTERVAL_FEASIBILITY = "evidence.interval_feasibility"
    EVIDENCE_COVERAGE = "evidence.coverage"
    PROVENANCE_SOURCE_VERIFIED = "provenance.source_verified"
    PROVENANCE_SELECTOR_VERIFIED = "provenance.selector_verified"


class EvidenceClass(Enum):
    CASE = "case"
    METHOD = "method"
    TRANSFER = "transfer"
    EXPERIMENTAL = "experimental"
    CORPUS = "corpus"
    BASELINE = "baseline"


class ActionLevel(Enum):
    REJECT_NONEXECUTABLE = 0
    RETAIN_BOUNDED_CLAIM = 1
    ALLOW_BOUNDED_QUERY = 2
    ALLOW_OPERATIONAL_USE = 3


@dataclass
class Object:
    object_id: str
    family: str
    geometry_parameters: dict[str, float]


@dataclass
class State:
    state_id: str
    domain: tuple[float, float]
    grid: list[float]


@dataclass
class Response:
    response_id: str
    units: str
    positivity_expected: bool = True


@dataclass
class Relation:
    relation_id: str
    functional_form: str
    coefficient_class: str  # e.g. "48 printed-magnitude permutations/signs"
    declared_domain: tuple[float, float]


@dataclass
class Predicate:
    predicate_id: str
    predicate_type: PredicateType
    expression: str
    declared_by: str  # mechanics argument or source statement
    result: Optional[bool] = None
    note: str = ""
    monotonicity_inapplicable: bool = False


@dataclass
class Evidence:
    evidence_id: str
    evidence_class: EvidenceClass
    cells: int
    rounding_half_unit: float
    source_ids: list[str] = field(default_factory=list)


@dataclass
class Provenance:
    source_id: str
    locator: str  # DOI / URL / local path
    sha256: str = ""
    accessed: str = ""
    license_boundary: str = ""


@dataclass
class Action:
    action_id: str
    level: ActionLevel
    scope: str
    open_gates: list[str] = field(default_factory=list)


@dataclass
class BoundedRelationRun:
    run_id: str
    object: Object
    state: State
    response: Response
    relation: Relation
    predicates: list[Predicate]
    evidence: list[Evidence]
    provenance: list[Provenance]
    action: Optional[Action] = None
    notes: list[str] = field(default_factory=list)