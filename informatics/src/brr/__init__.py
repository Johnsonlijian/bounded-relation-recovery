"""BRR: Bounded Relation Recovery — typed protocol package skeleton.

Mirrors reports/r04_brr_protocol_schema.md. The package intentionally keeps the data
model declarative so that manuscript text, JSON records and executable checks share one
source of truth. Import cost is minimal (dataclasses + stdlib only).
"""

from .schema import (  # noqa: F401
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
from .actions import reduce_action  # noqa: F401