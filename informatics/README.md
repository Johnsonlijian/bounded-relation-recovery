# Informatics artefact — bounded relation recovery protocol

Submission-facing bundle for *Advanced Engineering Informatics*. The manuscript contribution is an **auditable action algebra** (`reject` / `retain bounded claim` / `allow bounded query`), not a new buckling formula. Cold-formed steel relations supply the evidence programme only.

## What this package contains

| File | Role |
|------|------|
| `knowledge_graph.json` | Typed ontology, provenance, evidence classes, method controls and node/rule graph |
| `outputs/knowledge_trace.csv` | Claim → rule → evidence → status trace (machine-readable audit log) |
| `outputs/design_query_examples.csv` | Six deterministic queries with printed vs recovered actions |
| `outputs/evidence_state.json` | Evidence gate summary for the angle programme |
| `outputs/result_summary.json` | Identification and replay numbers regenerated from public tables |
| `outputs/r02_protocol_validation_summary.json` | Positive control + 15 injected cases + perturbation summary |
| `outputs/r04_sr_baseline_summary.json` | Unconstrained-fit baseline on the same 20 rounded cells |
| `outputs/r04_dsm_demo_summary.json` | Direct Strength Method local-module demonstration |
| `src/brr/schema.py` | Stable typed schema (`PredicateType`, `ActionLevel`, dataclasses) |
| `src/brr/actions.py` | Action reduction logic (one action per run) |
| `ACTION_TRACE_GUIDE.md` | How to read the trace and query files |
| `REPRODUCIBLE_RUNBOOK.md` | Commands to regenerate the artefact from the project root |
| `MANIFEST.json` | SHA-256 checksums for the files above |

## How to inspect without rerunning anything

1. Open `knowledge_graph.json` and read `provenance`, `evidence_classes` and `method_controls`.
2. Open `outputs/knowledge_trace.csv` — each row is one auditable claim with its rule, evidence pointer and status.
3. Open `outputs/design_query_examples.csv` — same protocol, six explicit `(a/t, a/b)` queries; note the printed route is always `reject_nonexecutable`.
4. Read `src/brr/actions.py` — the state machine in the manuscript figure is a direct rendering of this reduction order.

## Evidence boundary (human-only gates remain open)

- Native Zhang et al. CUFSM model files are **not** redistributed.
- AISI RP23-01 PDF and CUFSM example MAT files are **not** redistributed; manifests record URLs and hashes.
- `human_engineer_review` is **closed** (`completed_2026-10-06`); `operational_use` remains **open** because native source CUFSM models are unavailable.
- Public mirror: https://github.com/Johnsonlijian/bounded-relation-recovery
- Package state: `LOCAL_ONLY / NOT_SUBMITTED`.

## Regeneration

See `REPRODUCIBLE_RUNBOOK.md`. Full regeneration requires the parent project tree (`data/`, `src/`, `external_sources/`). This folder is the **submission slice** of that tree.

## Citation

If the manuscript is accepted, cite the paper DOI once assigned. Until then, treat this bundle as a private submission artefact tied to the local candidate manuscript dated October 2026.
