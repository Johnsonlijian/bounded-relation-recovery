# Bounded release calculus — public reproducibility candidate

Software and derived artefacts for the manuscript *Bounded release calculus: an action-preserving semantics for published engineering relations*. The central contribution is a typed, monotone-blocking action semantics that binds evidence, provenance and selectors to one computational permission.

## Evidence programme

- Zhang et al. lipped-angle relation: 48 printed-magnitude candidates, 630 published replay cells and a bounded geometry-to-response reconstruction.
- AISI RP23-01 lipped-channel relation: selector/corner transfer sample; the query remains bounded.
- Uzer (2024) geotechnical relation family: 445 admissible oedometer cells and nine attributed e0-only correlations; 2 reject on positivity, 7 retain bounded claims under the displayed 0.0005 interval.

Native Zhang CUFSM model files and the Uzer authors' original spreadsheet are not redistributed. See evidence/cufsm_rerun_boundary.md and informatics/ for the submission slice and gate statements.

## R10 controls

The R10 extension records deterministic reduction, monotone blocking, groupwise
scale feasibility, same-source cross-table transfer and the fact that
operational use is outside the computational closure. It contains 48 declared
angle candidates, 630 Zhang table cells and 445 admissible geotechnical cells.

## Quick start

    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv/Scripts/activate
    pip install -r requirements.txt
    python src/analyze_rebuild.py
    python src/r07_compression_index_case.py
    python src/r09_augment_geotechnical_graph.py
    python src/r10_super_uplift_evidence.py
    python -m brr.evaluate --self-test

Full regeneration, including optional GNU Octave steps, is in REPRODUCIBLE_RUNBOOK.md.

## Data and release boundary

The current R10 extension is staged in this local worktree and has not been
pushed or uploaded. The existing GitHub/Zenodo record, if used, covers an
earlier release and must be refreshed only after review. Code is MIT;
transcribed numeric tables remain subject to the source licences in
DATASETS_AND_LINKS.csv.

## Citation

Use CITATION.cff; add a paper DOI only after acceptance.
