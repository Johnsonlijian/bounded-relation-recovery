# Bounded release calculus: public reproducibility package

Software and derived artefacts for the manuscript *Bounded release calculus: an action-preserving
semantics for published engineering relations*.

The contribution is a typed, monotone-blocking action semantics for published engineering relations.
A contract binds a relation to its declared domain, displayed precision, finite candidate class and
provenance; a fixed reducer returns exactly one computational permission:

| Action | Meaning |
|---|---|
| `REJECT_NONEXECUTABLE` | a mechanics or source-verification blocker fails |
| `RETAIN_BOUNDED_CLAIM` | the evidence does not license a query |
| `ALLOW_BOUNDED_QUERY` | one candidate is identified and every gate passes |

Operational design use is outside the computational image and is never emitted.

## Evidence programme

Three heterogeneous contracts reach those actions through one interface:

- **Zhang et al. lipped-angle relation** — the printed expression is negative on its declared domain
  and is rejected before fitting; one of 48 printed-magnitude assignments is interval-feasible; over
  the 630 published response cells all four groupwise scale intervals are non-empty while their
  common intersection is empty; an unconstrained fit reaches a *smaller* residual than the recovered
  assignment and still cannot recover the printed magnitudes.
- **AISI RP23-01 lipped-channel relation** — the query is withheld while the mode selector and the
  corner idealisation remain open.
- **Uzer (2024) geotechnical relation family** — 445 admissible cells and nine attributed
  `e0`-only compression-index correlations: two reject on positivity, seven retain bounded claims
  under the displayed 0.0005 interval.

## Repository layout

    data/                 derived transcription and search tables
    figures/              figure masters (PDF/SVG/PNG) and superseded variants
    informatics/          submission-facing informatics slice, with MANIFEST.json
    external_sources/     provenance records and local run scripts (no third-party binaries)
    src/                  analysis, evaluator and figure generators
    src/brr/              typed schema, action reducer and reference evaluator
    outputs/              derived results, control records and summaries

## Quick start

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv/Scripts/activate
    pip install -r requirements.txt
    python src/analyze_rebuild.py
    python src/r07_compression_index_case.py
    python src/r09_augment_geotechnical_graph.py
    python src/r10_super_uplift_evidence.py
    python -m brr.evaluate --self-test

Full regeneration, including the optional GNU Octave finite-strip steps, is documented in
`REPRODUCIBLE_RUNBOOK.md`.

## Data and release boundary

The transcribed numeric tables derive from published sources and remain subject to those sources'
licences; see `DATASETS_AND_LINKS.csv` for every DOI, URL, hash and redistribution decision.

Not redistributed here: the native Zhang et al. CUFSM model files, third-party CUFSM example inputs
and `.mat` files, and the AISI RP23-01 report PDF. The 630-cell geometry rebuild is a consistency
check under a declared frozen effective modulus, not a recovery of the authors' original model.

The engineering review recorded in `evidence/` is an **author self-review**. It is not an independent
review, and no independent engineering sign-off is claimed.

## Citation

Use `CITATION.cff`. Code is MIT licensed.
