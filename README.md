# Bounded relation recovery — public reproducibility package

Software and derived artefacts for the manuscript *Bounded relation recovery: an auditable action contract for published engineering relations* (candidate submission to *Advanced Engineering Informatics*).

This repository contains the **informatics artefact only**: typed knowledge graph, action trace, schema code, transcribed public tables, derived summaries, and regeneration scripts. It does **not** include the manuscript PDF, cover letter, or third-party CUFSM model files.

## What this repo proves

- One auditable action per protocol run: `reject` / `retain bounded claim` / `allow bounded query`
- Cold-formed steel relations are an **evidence programme**, not a new buckling formula
- Native Zhang et al. CUFSM models are **not** redistributed; a **bounded** public-CUFSM reconstruction of 630 published cells is provided instead

See `evidence/cufsm_rerun_boundary.md` for the CUFSM rerun boundary.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/analyze_rebuild.py
python src/r06_action_state_machine.py
python src/r06_export_figure_pdfs.py
```

Full regeneration, including optional GNU Octave CUFSM steps: `REPRODUCIBLE_RUNBOOK.md`.

## Directory map

| Path | Role |
|------|------|
| `knowledge_graph.json` | Typed ontology, provenance, evidence classes |
| `informatics/` | Submission-facing slice with manifest and trace guide |
| `src/brr/` | Action schema and reduction logic |
| `data/` | Transcribed public tables (not native CUFSM models) |
| `outputs/` | Derived summaries and trace tables |
| `figures/` | Vector figure masters |
| `evidence/` | Human sign-off and CUFSM boundary notes |

## External dependencies

Clone MIT-licensed CUFSM before Octave reruns:

```bash
git clone https://github.com/thinwalled/cufsm-git external_sources/cufsm-git
cd external_sources/cufsm-git && git checkout d16e28195d3963ee218be0768e19159b0777fdee
```

## Data availability (manuscript citation)

Cite this repository in the manuscript data statement:

> https://github.com/Johnsonlijian/bounded-relation-recovery (release commit `84b3e3f`, 2026-10-06)

A Zenodo archive DOI may be minted on acceptance if the journal requests a DOI-backed deposit.

## Citation

Use `CITATION.cff`. Paper DOI will be added on acceptance.

## License

Code: MIT (`LICENSE`). Transcribed numeric tables are derived from published sources listed in `DATASETS_AND_LINKS.csv`; verify publisher terms before reuse.
