# Reproducible runbook — informatics artefact (October 2026)

## Scope

Regenerates the typed knowledge graph, action trace, query examples, protocol controls, unconstrained-fit baseline, DSM demonstration slice, and vector figures from **public table transcriptions** and documented external manifests. No new cross-section families are introduced in this bundle.

Parent project root: one level above `submission/INFORMATICS_ARTEFACT/`.

## Environment

- Python 3.11+
- NumPy, pandas, Matplotlib
- GNU Octave (only for CUFSM reconstruction / RP23-01 reruns under `external_sources/`)
- LaTeX with `elsarticle` (manuscript PDF)

Record `python --version` and package versions in a dated run log before freezing a release candidate.

## Core protocol regeneration (Python only)

From the project root:

```powershell
python src/analyze_rebuild.py
python src/r02_protocol_stress_tests.py
python src/r02_external_relation_transfer.py
python src/r04_sr_baseline.py
python src/r04_dsm_demo.py
python src/r06_action_state_machine.py
python src/r06_package_informatics.py
```

Expected core outputs:

- `knowledge_graph.json`
- `outputs/knowledge_trace.csv`
- `outputs/design_query_examples.csv`
- `outputs/evidence_state.json`
- `outputs/result_summary.json`
- `outputs/r02_protocol_validation_summary.json`
- `outputs/r04_sr_baseline_summary.json`
- `outputs/r04_dsm_demo_summary.json`
- `figures/figure_action_state_machine.{svg,pdf}`
- `submission/INFORMATICS_ARTEFACT/` (refreshed copy + `MANIFEST.json`)

## Extended evidence programme (optional Octave)

```powershell
python src/r02_cufsm_transfer.py
python src/r03_zhang_model_reconstruction.py summarize
python src/r03_ksce_spectrum_transfer.py
python src/r04_rp23001_rebuild.py
python src/r05_figures.py
```

These regenerate bounded reconstruction, transfer screens and manuscript Figures 2, 8–10. They do **not** change the action algebra.

## LaTeX

```powershell
cd manuscript
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

## Acceptance checks

| Check | Expected |
|-------|----------|
| Angle winner | `+0.292 -0.339 x^2 +1.060 x` |
| Printed route | `reject_nonexecutable` on all six query examples |
| Recovered route | `allow_bounded_query` on the same six queries |
| SR baseline RMSE | 0.001584 MPa (joint LS) vs 0.001669 MPa (protocol) |
| DSM demo | recovered φ_l within 0.013%; printed non-executable |
| Channel programme | `retain_bounded_claim` after independent selector sample |

## Evidence boundary

`LOCAL_ONLY / NOT_SUBMITTED`. Native author CUFSM files, batch modulus metadata and operational engineering sign-off remain outside this artefact. The runbook documents regeneration; it is not an editorial decision or upload receipt.
