# Reproducible runbook — protocol-centered local candidate (2026-10-04)

## Scope

This runbook regenerates the knowledge graph, the 48-candidate search, interval margins, public-table replay summaries, query trace, residual diagnostics, protocol stress tests, public-solver transfer evidence and all seven vector figures, the bounded 630-cell Zhang source-model reconstruction and the independent KSCE spectrum-transfer screen from the included public-table transcriptions and the separately sourced CUFSM example manifest. The public-solver transfer check does not rerun the Zhang et al. models and does not establish cross-object relation recovery.

## Environment

- Python 3.11.15
- NumPy 2.2.6
- pandas 2.3.3
- Matplotlib 3.11.0 (the script uses the `tick_labels` keyword for the installed Matplotlib API)
- GNU Octave 10.2.0 (used only for the documented public-CUFSM compatibility rerun)
- LaTeX with `elsarticle`, `lmodern`, `amsmath`, `booktabs`, `tabularx`, `graphicx`, `microtype`, `xurl` and `hyperref`

The versions above were recorded from the active Windows environment on 2026-10-03. They identify the local regeneration environment; they do not certify cross-platform or independent CUFSM equivalence.

Record exact package versions and the operating system in a dated run log before a release candidate is frozen.

## Clean regeneration

From this project root:

```powershell
python src/analyze_rebuild.py
python src/r02_protocol_stress_tests.py
python src/r02_cufsm_transfer.py
python src/r02_external_relation_transfer.py
python src/r03_zhang_model_reconstruction.py summarize
python src/r03_ksce_spectrum_transfer.py
```

Expected regenerated files include:

- `knowledge_graph.json`
- `outputs/result_summary.json`
- `outputs/evidence_state.json`
- `outputs/design_query_examples.csv`
- `outputs/knowledge_trace.csv`
- `outputs/candidate_sensitivity.csv`
- `outputs/replay_residual_summary.csv`
- `outputs/candidate_search_48_recomputed.csv`
- `outputs/identification_margin_recomputed.csv`
- `outputs/full_cufsm_replay_recomputed.csv`
- `outputs/full_cufsm_group_replay_recomputed.csv`
- `outputs/r02_failure_injection_results.csv`
- `outputs/r02_case_sensitivity_and_ablation.csv`
- `outputs/r02_digit_perturbation_trials.csv`
- `outputs/r02_evidence_manifest.csv`
- `outputs/r02_protocol_validation_summary.json`
- `outputs/r02_cufsm_transfer_curve.csv`
- `outputs/r02_cufsm_transfer_summary.json`
- `outputs/r02_cufsm_public_source_manifest.json`
- `outputs/r02_external_relation_transfer.csv`
- `outputs/r02_external_relation_transfer_summary.json`
- `figures/figure1_knowledge_to_action.{svg,pdf,png}`
- `figures/figure2_admissibility_and_replay.{svg,pdf,png}`
- `figures/figure3_full_table_shape_replay.{svg,pdf,png}`
- `figures/figure4_replay_error_boundary.{svg,pdf,png}`
- `figures/figure5_protocol_stress_tests.{svg,pdf,png}`
- `figures/figure6_public_cufsm_transfer.{svg,pdf,png}`
- `figures/figure7_external_relation_transfer.{svg,pdf,png}`

The analysis script reads only `data/source_table_transcription.csv` and `data/full_cufsm_cells.csv` for the lipped-angle numerical recomputation. The R02 stress-test script generates a known-form control, 15 injected cases, 200 deterministic perturbations, leave-source subsets and a predicate ablation. The public-solver transfer script compares the public repository example `cnolip_P.mat` with the documented rerun when the non-redistributed local input and rerun MAT files are present; the source manifest records the repository commit and hashes, while the derived curve and summary are included in the package. The external relation script evaluates the AISI RP23-01 relation card from the locally held source PDF; it tests object and predicate transfer but does not rerun the report's FSM sections. The R03 source-model reconstruction uses the four local Octave chunk runs in `external_sources/zhang_reconstruction/r03_zhang_cufsm_run.m` and then `python src/r03_zhang_model_reconstruction.py summarize`; its frozen `E_eff`, mesh and wavelength contract are recorded in `external_sources/zhang_reconstruction/r03_reconstruction_provenance.json`. The KSCE screen runs `external_sources/zhang_reconstruction/r03_ksce_spectrum_transfer.m` and is summarized by `python src/r03_ksce_spectrum_transfer.py`. The lipped-angle winner should remain `+0.292 -0.339 x^2 +1.060 x`; the displayed half-unit is `0.005 MPa`; the required common half-width is approximately `0.003127740 MPa`.

## LaTeX build and visual QA

From `manuscript`:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
```

Inspect the PDF page count, embedded fonts, equation references, figure labels and captions, and render every page to PNG before delivery. Synchronise only verified source/PDF/figure outputs into `submission` and `FINAL_SUBMISSION_PACKAGE_2026-09-26`.

## Evidence boundary

The manuscript was submitted on 2026-10-07 and the curated package is published; this working area is not itself a release artefact. Native Zhang et al. CUFSM files and the source batch modulus remain unavailable; the bounded independent reconstruction closes only the published Table 4/Table 8 geometry-to-response scope under its frozen metadata contract. The KSCE screen is a nearest-spectrum transfer check rather than mode-selector recovery. Independent human engineer review, live journal instructions, licensing and repository metadata remain open gates. No file in this runbook is an upload receipt or editorial decision.
