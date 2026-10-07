# Action trace guide

Each trace row binds a typed source contract to one reducer action. The key
fields are the source locator, object and response types, declared domain,
candidate class, displayed half-unit, predicate statuses, selector/provenance
state, evidence class and final action.

Predicate status is `1` (passed), `0` (failed) or `BOX` (open/unevaluated).
The reducer applies blocker priority first: a mechanics or source-verification
failure rejects; a singleton feasible candidate with closed evidence permits a
bounded query; all other incomplete, empty or multiply feasible cases remain
bounded claims. The trace does not authorize member design or operational use.
