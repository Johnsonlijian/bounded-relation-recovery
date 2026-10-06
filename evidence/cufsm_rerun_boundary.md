# CUFSM rerun boundary — what is and is not publicly reproducible

## Short answer

| Gate | Status | Reason |
|------|--------|--------|
| **Original Zhang et al. CUFSM model rerun** | **Not available** | Authors did not publish native MATLAB/CUFSM model files or batch modulus metadata |
| **Bounded geometry-to-response reconstruction (630 cells)** | **Available** | Public geometry ratios + MIT `cufsm-git` + declared `E_eff` contract |
| **Public CUFSM solver transfer (500 cells)** | **Available** | `thinwalled/cufsm-git` example `cnolip_P.mat` |
| **KSCE 2023 spectrum screen (24 rows)** | **Available (bounded)** | Nearest-spectrum predicate; source mode selector not published |

## Open-source CUFSM used in this project

| Item | Value |
|------|-------|
| Repository | https://github.com/thinwalled/cufsm-git |
| License | MIT |
| Pinned commit | `d16e28195d3963ee218be0768e19159b0777fdee` |
| Local wrapper | `external_sources/cufsm_octave_compat/analysis/stripmain.m` |
| Zhang reconstruction driver | `external_sources/zhang_reconstruction/r03_zhang_cufsm_run.m` |

## What Zhang et al. (2022) did publish

- Equations and rounded Tables 4, 5, 8, 9 in *Buildings* 12:712, DOI [10.3390/buildings12060712](https://doi.org/10.3390/buildings12060712)
- Geometry ratios and 630 stress cells sufficient for **transcription** and **independent rebuild under a frozen contract**

## What they did not publish

- Native CUFSM `.mat` model files
- Batch elastic modulus used in their CUFSM5 runs
- Mode-selection metadata needed for bit-for-bit reproduction

Therefore **no public archive can rerun the authors' exact models**. The defensible public route is the bounded reconstruction already implemented in `src/r03_zhang_model_reconstruction.py`.

## Bounded reconstruction contract (frozen)

- `E_eff = 217400` MPa (calibrated from four sentinel rows; not claimed as authors' batch modulus)
- `t = 2` mm, mesh target 4 mm, ν = 0.30
- 32 wavelength points on `0.30a`–`1.60a`
- First positive eigenvalue minimum with log-domain quadratic interpolation

**Result:** 630/630 rows within predeclared 5% screen; overall RMSE **0.532%**; max **2.431%**.

## How to rerun the available parts

```powershell
git clone https://github.com/thinwalled/cufsm-git external_sources/cufsm-git
cd external_sources/cufsm-git
git checkout d16e28195d3963ee218be0768e19159b0777fdee

python src/r02_cufsm_transfer.py
python src/r03_zhang_model_reconstruction.py prepare
octave-cli --no-gui --quiet --eval "addpath('external_sources/zhang_reconstruction'); addpath('external_sources/cufsm_octave_compat'); r03_zhang_cufsm_run(1,4)"
# repeat chunks 2–4
python src/r03_zhang_model_reconstruction.py summarize
```

## Manuscript-safe wording

- **Do say:** independent bounded reconstruction of published Table 4/8 cells using public CUFSM under a declared metadata contract.
- **Do not say:** independent rerun of the authors' original CUFSM models.
