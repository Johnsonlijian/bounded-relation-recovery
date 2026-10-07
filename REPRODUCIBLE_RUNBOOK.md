# Reproducible runbook — R10 bounded-release calculus (7 October 2026)

## Scope

Regenerates the typed knowledge graph, action trace, query examples, protocol controls, bounded Zhang reconstruction summaries, selector transfer records, the geotechnical direct-response case and R10 bounded-release controls from public table transcriptions and documented source manifests. No original Zhang CUFSM model files or Uzer spreadsheet are included.

## Environment

- Python 3.11+
- NumPy, pandas, Matplotlib, pypdf
- GNU Octave only for optional CUFSM reconstruction / RP23-01 reruns
- LaTeX with `elsarticle` for manuscript PDFs

## Core run (Python)

From the project root:

```powershell
python src/analyze_rebuild.py
python src/r02_protocol_stress_tests.py
python src/r02_external_relation_transfer.py
python src/r04_sr_baseline.py
python src/r04_dsm_demo.py
python src/r06_action_state_machine.py
python src/r07_compression_index_case.py
python src/r06_extend_artefact.py
python src/r09_augment_geotechnical_graph.py
python src/r10_super_uplift_evidence.py
python src/r06_package_informatics.py
python -m brr.evaluate --self-test
```

Expected headline records:

- angle candidate class: 48; retained relation `+0.292 -0.339 x^2 +1.060 x`; required half-width `0.003127740 MPa`;
- Zhang public held-out replay: 630 cells; bounded reconstruction RMSE `0.532%` under the frozen modulus contract;
- geotechnical table: 445 admissible cells, 9 attributed correlations, `2 REJECT_NONEXECUTABLE`, `7 RETAIN_BOUNDED_CLAIM`;
- action algebra: one reducer in `src/brr/actions.py` for all cases.
- R10 controls: three deterministic actions, monotone blocking pass, false global-scale feasibility, two same-source transfer rows, and no emitted operational action.

## Extended structural evidence (optional Octave)

```powershell
python src/r02_cufsm_transfer.py
python src/r03_zhang_model_reconstruction.py summarize
python src/r03_ksce_spectrum_transfer.py
python src/r04_rp23001_rebuild.py
python src/r05_figures.py
```

These steps do not close the native-source-model or human-engineering gates.

## LaTeX

```powershell
cd manuscript
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode supplement.tex
bibtex supplement
pdflatex -interaction=nonstopmode supplement.tex
pdflatex -interaction=nonstopmode supplement.tex
```

## Evidence boundary

`LOCAL_ONLY / NOT_SUBMITTED / HUMAN_ENGINEERING_GATE_OPEN`. Any public
GitHub/Zenodo record preceding this R10 candidate must be refreshed and
reviewed before external upload. The runbook is a regeneration contract, not
an editorial receipt or engineering approval.
