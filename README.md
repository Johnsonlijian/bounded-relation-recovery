# Bounded relation recovery — reproducibility candidate

Software and derived artefacts for the manuscript Bounded relation recovery: an auditable action contract for published engineering relations. The central contribution is a typed action reducer (reject / retain bounded claim / allow bounded query), not a new design formula.

## Evidence programme

- Zhang et al. lipped-angle relation: 48 printed-magnitude candidates, 630 published replay cells and a bounded geometry-to-response reconstruction.
- AISI RP23-01 lipped-channel relation: selector/corner transfer sample; the query remains bounded.
- Uzer (2024) geotechnical relation family: 445 admissible oedometer cells and nine attributed e0-only correlations; 2 reject on positivity, 7 retain bounded claims under the displayed 0.0005 interval.

Native Zhang CUFSM model files and the Uzer authors' original spreadsheet are not redistributed. See evidence/cufsm_rerun_boundary.md and informatics/ for the submission slice and gate statements.

## Quick start

    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv/Scripts/activate
    pip install -r requirements.txt
    python src/analyze_rebuild.py
    python src/r07_compression_index_case.py
    python src/r09_augment_geotechnical_graph.py
    python -m brr.evaluate --self-test

Full regeneration, including optional GNU Octave steps, is in REPRODUCIBLE_RUNBOOK.md.

## Data and release boundary

The current R09 extension is staged in this local worktree and has not been pushed or uploaded. The existing GitHub/Zenodo record covers the preceding angle/channel release and must be refreshed only after review. Code is MIT; transcribed numeric tables remain subject to the source licences in DATASETS_AND_LINKS.csv.

## Citation

Use CITATION.cff; add a paper DOI only after acceptance.
