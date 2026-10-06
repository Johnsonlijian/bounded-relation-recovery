# Action trace guide

## Purpose

The protocol returns **one action per run**. The trace files make that action inspectable without re-running solvers or fits.

## `outputs/knowledge_trace.csv`

Columns:

| Column | Meaning |
|--------|---------|
| `claim` | Plain-language statement being audited |
| `knowledge_rule` | Rule id in the graph (R1–R8 or method/transfer gate label) |
| `evidence` | What was actually checked (cell counts, domains, manifests) |
| `status` | Outcome label (`rejected`, `supported`, `bounded_*`, `not_claimed`, etc.) |

Example rows (abbreviated):

- **Printed route executable** → `R1` → 20 rounded cells → `rejected` (shape negative on domain).
- **Identified assignment compatible** → `R4` → 4/4 groups at 0.005 MPa → `supported_within_candidate_class`.
- **CUFSM independently rerun** → scope gate → native files unavailable → `not_claimed`.

The trace is **not** a performance log. It does not rank relations by RMSE.

## `outputs/design_query_examples.csv`

Each row is a deterministic query on the lipped-angle programme:

| Column | Meaning |
|--------|---------|
| `a_over_t`, `a_over_b` | Query coordinates |
| `printed_shape`, `identified_shape` | Shape evaluation at the query point |
| `printed_action`, `identified_action` | Protocol actions for the two relations |
| `operational_gate` | Always open in this study (`independent CUFSM rerun + human engineer review`) |

The contrast between `reject_nonexecutable` (printed) and `allow_bounded_query` (recovered) is the engineering informatics result for this object.

## `knowledge_graph.json`

Key sections:

- `provenance` — source DOI, what was and was not rerun, reconstruction boundaries.
- `evidence_classes` — `case`, `method`, `transfer` (not pooled into one accuracy score).
- `method_controls` — positive control, 15 injected failures, 200 digit perturbations.
- `nodes` / `rules` — typed objects and compiled predicates.

## Action levels (`src/brr/schema.py`)

| Level | Name | When emitted |
|-------|------|--------------|
| 0 | `reject_nonexecutable` | Mechanics or provenance predicate fails |
| 1 | `retain_bounded_claim` | Predicates incomplete, selector mismatch, or hold-out not contract-matched |
| 2 | `allow_bounded_query` | All declared predicates pass inside tested scope |
| 3 | `allow_operational_use` | **Not granted** by the computational layer in this study |

Reduction order is implemented in `src/brr/actions.py` and illustrated in manuscript Figure `fig:statemachine`.

## Mapping to manuscript evidence programme

| Programme row | Typical trace / query signal |
|---------------|------------------------------|
| Printed angle expression | `reject_nonexecutable` on printed route |
| Recovered angle assignment | `allow_bounded_query` in query examples; bounded replay in trace |
| Unconstrained quadratic fit | Not an action; see `r04_sr_baseline_summary.json` |
| Channel compression / bending | Predicate pass, independent sample → `retain_bounded_claim` (see main text) |
| Complex-edge spectrum screen | `bounded_transfer_pass` in trace |
