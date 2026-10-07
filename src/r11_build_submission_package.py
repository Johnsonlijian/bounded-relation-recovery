"""Build the R11 final-check submission candidate (local only; no push, no upload).

Differences from the R10 builder:
  * the figure set is the five figures the manuscript actually includes
    (figure10_argument is no longer used);
  * the manuscript, supplement, bibliography and informatics artefact are taken
    from the post-check working tree.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "FINAL_SUBMISSION_PACKAGE_2026-10-07_R11"
ZIP = ROOT / "AEI_KNOWLEDGE_ENGINEERING_REBUILD_2026-10-07_R11_FINAL.zip"

FILES = [
    ("manuscript/main.tex", ROOT / "manuscript/main.tex"),
    ("manuscript/main.pdf", ROOT / "manuscript/main.pdf"),
    ("manuscript/supplement.tex", ROOT / "manuscript/supplement.tex"),
    ("manuscript/supplement.pdf", ROOT / "manuscript/supplement.pdf"),
    ("manuscript/references.bib", ROOT / "manuscript/references.bib"),
    ("submission/title_page.tex", ROOT / "submission/title_page.tex"),
    ("submission/title_page.pdf", ROOT / "submission/title_page.pdf"),
    ("submission/cover_letter.tex", ROOT / "submission/cover_letter.tex"),
    ("submission/cover_letter.pdf", ROOT / "submission/cover_letter.pdf"),
    ("submission/highlights.txt", ROOT / "submission/highlights.txt"),
    ("submission/graphical_abstract.pdf", ROOT / "submission/graphical_abstract.pdf"),
    ("submission/graphical_abstract.svg", ROOT / "submission/graphical_abstract.svg"),
    ("submission/graphical_abstract.png", ROOT / "submission/graphical_abstract.png"),
    ("submission/target_positioning_2026-10-07_R10.md", ROOT / "submission/target_positioning_2026-10-07_R10.md"),
    ("submission/AEI_author_instructions_audit_2026-10-07_R10.md", ROOT / "submission/AEI_author_instructions_audit_2026-10-07_R10.md"),
]

FIGURE_STEMS = [
    "figure12_bounded_release_calculus",
    "figure13_scale_nonidentification",
    "figure2_admissibility_and_replay",
    "figure9_two_relations",
    "figure11_geotechnical_case",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if PKG.exists():
        shutil.rmtree(PKG)
    if ZIP.exists():
        ZIP.unlink()
    PKG.mkdir(parents=True)
    rows = []
    for rel, src in FILES:
        if not src.exists():
            raise FileNotFoundError(src)
        dst = PKG / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    for stem in FIGURE_STEMS:
        for ext in (".pdf", ".svg"):
            src = ROOT / "figures" / f"{stem}{ext}"
            if src.exists():
                dst = PKG / "figures" / f"{stem}{ext}"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    art_dst = PKG / "submission" / "INFORMATICS_ARTEFACT"
    shutil.copytree(ROOT / "submission" / "INFORMATICS_ARTEFACT", art_dst)
    readme = PKG / "README.md"
    readme.write_text(
        """# AEI Knowledge Engineering Rebuild - R11 final-check candidate

State: LOCAL_ONLY / NOT_SUBMITTED / HUMAN_ENGINEERING_GATE_OPEN

This candidate is the post-check revision of the bounded-release calculus paper.
The check round changed only presentation, attribution and figure engineering; no
numerical result was recomputed or altered.

Figure names in this package are source names, not manuscript numbers. The mapping is:

  figure12_bounded_release_calculus.pdf   -> manuscript Figure 1 (calculus + gate controls)
  figure13_scale_nonidentification.pdf    -> manuscript Figure 2 (groupwise scale intervals)
  figure2_admissibility_and_replay.pdf    -> manuscript Figure 3 (angle evidence)
  figure9_two_relations.pdf               -> manuscript Figure 4 (channel-contract controls)
  figure11_geotechnical_case.pdf          -> manuscript Figure 5 (geotechnical case)

The five figure masters shipped here are byte-identical to the figures embedded in
manuscript/main.pdf. Third-party source files (Zhang et al. CUFSM models, the CUFSM
example inputs, the AISI RP23-01 report, the Uzer spreadsheet) are not redistributed;
source URLs, hashes and licences are recorded in DATASETS_AND_LINKS.csv.

External GitHub/Zenodo refresh, journal upload and operational engineering approval
remain open. Regeneration commands are in
submission/INFORMATICS_ARTEFACT/REPRODUCIBLE_RUNBOOK.md.
""",
        encoding="utf-8",
    )
    for path in sorted(PKG.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.csv":
            rows.append((str(path.relative_to(PKG)).replace("\\", "/"), digest(path), path.stat().st_size))
    sums = PKG / "SHA256SUMS.csv"
    with sums.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "sha256", "bytes"])
        w.writerows(sorted(rows))
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(PKG.rglob("*")):
            if path.is_file():
                rel = path.relative_to(PKG).as_posix()
                info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (0o100644 & 0xFFFF) << 16
                zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"package: {PKG}")
    print(f"files: {len(rows)}")
    print(f"zip: {ZIP} ({ZIP.stat().st_size} bytes)")
    print(f"zip sha256: {digest(ZIP)}")


if __name__ == "__main__":
    main()
