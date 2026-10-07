# INFORMATICS_ARTEFACT — bounded relation recovery

Submission-facing informatics bundle for *Bounded relation recovery: an auditable action contract for published engineering relations*. The contribution is an executable action algebra (`reject_nonexecutable` / `retain_bounded_claim` / `allow_bounded_query`), not a new design formula.

## Contents

- `knowledge_graph.json`: typed objects, predicates, provenance, evidence classes and one run record per executed relation.
- `outputs/knowledge_trace.csv`: claim-to-rule-to-evidence trace, including the cross-domain case.
- `outputs/design_query_examples.csv` and `outputs/channel_query_examples.csv`: deterministic structural examples.
- `outputs/r07_compression_index_contract.json` and `outputs/r07_compression_index_dataset.csv`: the Uzer (2024) geotechnical case (445 cells; 2 rejects, 7 bounded retains).
- `src/brr/`: stable schema, reducer and reference evaluator; `run_scalar_correlation_protocol` executes direct-response correlations through the same reducer.
- `src/r07_compression_index_case.py`: regenerates the geotechnical contract and transcription from the archived source PDF.
- `REPRODUCIBLE_RUNBOOK.md`, `ACTION_TRACE_GUIDE.md` and `MANIFEST.json`.

## Regeneration

From the parent project root:

```powershell
python src/analyze_rebuild.py
python src/r06_extend_artefact.py
python src/r07_compression_index_case.py
python src/r09_augment_geotechnical_graph.py
python src/r06_package_informatics.py
python -m brr.evaluate --self-test
```

The geotechnical case uses the observed printed-table domain `0.454 <= e0 <= 2.018` and displayed half-unit `0.0005`. It is a direct-response evidence test; no positive scale or numerical solver selector is invented.

## Evidence boundaries

Native Zhang et al. CUFSM model files and the Uzer authors' original spreadsheet are not redistributed. The Zhang response path is a bounded reconstruction with a frozen effective modulus; the geotechnical input is a machine transcription of the printed table. `human_engineer_review` remains an author self-review, with no independent third-party sign-off claimed. Operational use remains gated.

Package state: `LOCAL_ONLY / NOT_SUBMITTED`.
