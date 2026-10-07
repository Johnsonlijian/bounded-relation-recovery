# Data and provenance

The CSV files in this directory are **transcriptions and derived inputs**, not the publisher's original CUFSM model files.

| File | Role | Provenance | Unit / key fields |
|---|---|---|---|
| `source_table_transcription.csv` | 20 primary equation-table cells | Zhang et al. (2022), Tables 5 and 9, version of record | stress in MPa; `a_over_t`, `a_over_b` |
| `full_cufsm_cells.csv` | 630 public replay cells | Zhang et al. (2022), Tables 4 and 8, version of record | stress in MPa; `a_over_t`, `a_over_b`, `c_over_a` |
| `signed_assignment_search_48.csv` | Candidate search result | Derived deterministically from the primary transcription | 48 coefficient position/sign assignments |
| `identification_margin.csv` | Interval separation | Derived deterministically from the primary transcription | MPa half-width |
| `rounding_compatibility.csv` | Rounding and ablation checks | Derived deterministically from the primary transcription | compatibility flags and error summaries |

A clean run starts from the two public-table transcriptions. `src/analyze_rebuild.py` recomputes the candidate enumeration and 630-cell replay directly from those two files; the other search and replay CSVs are retained audit references and comparison fixtures. The source article reports CUFSM5 calculations, but the native model files are not present here; therefore the outputs are a public-table replay. Do not cite these CSVs as an independent finite-strip simulation.

The input records preserve the source DOI and page/table locators. R02 method-control and public-solver transfer outputs are derived artifacts; the public CUFSM example input and rerun MAT file remain in the local external-source area and are not redistributed. Licensing and repository policy are recorded per item in `DATASETS_AND_LINKS.csv`; the published repository is the curated release, not this working folder.


## R03 source-model recreation and independent case transfer

`outputs/r03_zhang_model_reconstruction.csv` is a bounded independent reconstruction of all 630 published Zhang Table 4/Table 8 local-buckling cells. It uses published geometry ratios, a frozen `E_eff=217400 MPa` because the source batch modulus is not stated, 4-mm strip target and 32 local-wavelength points. The result passes the predeclared 5% screen but does not claim native author model files.

`external_sources/zhang_reconstruction/ksce2023_table2_distortional_cases.csv` and `outputs/r03_ksce2023_spectrum_transfer.csv` provide a second published complex-edge source screen: 24 rows, nearest-spectrum predicate, 10% tolerance. This is transfer evidence, not a universal distortional-buckling recovery.
