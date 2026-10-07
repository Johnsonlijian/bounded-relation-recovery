# Action trace guide

The protocol returns one action per relation run. `outputs/knowledge_trace.csv` links each claim to its rule, evidence and status; it is not a pooled accuracy table.

## Action levels

| Level | Name | Trigger |
|---|---|---|
| 0 | `REJECT_NONEXECUTABLE` | mechanics or source-provenance predicate fails |
| 1 | `RETAIN_BOUNDED_CLAIM` | evidence, coverage, selector or direct-response interval remains incomplete |
| 2 | `ALLOW_BOUNDED_QUERY` | declared predicates pass inside the tested scope |
| 3 | `ALLOW_OPERATIONAL_USE` | never granted by the computational layer |

`src/brr/actions.py` is the single reducer. `src/brr/evaluate.py` computes typed predicates before calling it.

## Executed cases

- Zhang lipped-angle relation: printed route rejects; one candidate in the 48-member class allows a bounded query within the declared evidence scope.
- AISI lipped-channel relation: mechanics and rounded-card predicates pass, but selector/corner evidence retains a bounded claim.
- Uzer geotechnical correlations: 445 cells over the observed `e0` domain; two candidates reject on positivity and seven retain bounded claims because none meets the displayed `0.0005` direct-response interval. The source has no numerical solver selector, so selector verification is recorded as not applicable rather than guessed.

Open operational gates are preserved in every run. No action record is a member-safety decision.
