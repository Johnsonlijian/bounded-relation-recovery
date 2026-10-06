"""Export manuscript-facing figure PDFs from existing SVG masters (no new analysis)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
MANUSCRIPT = ROOT / "manuscript"
SUBMISSION = ROOT / "submission"

MANUSCRIPT_FIGURES = [
    "figure_action_state_machine",
    "figure8_action_contract",
    "figure2_admissibility_and_replay",
    "figure9_two_relations",
    "figure10_argument",
]


def svg_to_pdf(svg: Path, pdf: Path) -> None:
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2pdf(url=str(svg), write_to=str(pdf))
        return
    except Exception:
        pass
    try:
        from svglib.svglib import svg2rlg  # type: ignore
        from reportlab.graphics import renderPDF  # type: ignore

        drawing = svg2rlg(str(svg))
        renderPDF.drawToFile(drawing, str(pdf))
        return
    except Exception as exc:
        raise RuntimeError(f"cannot convert {svg} to PDF: {exc}") from exc


def sync_pdf(stem: str) -> None:
    candidates = [
        FIG / f"{stem}.pdf",
        MANUSCRIPT / f"{stem}.pdf",
    ]
    svg = FIG / f"{stem}.svg"
    if not svg.exists():
        svg = MANUSCRIPT / f"{stem}.svg"
    pdf = FIG / f"{stem}.pdf"
    if not pdf.exists():
        if not svg.exists():
            raise FileNotFoundError(f"missing SVG/PDF for {stem}")
        svg_to_pdf(svg, pdf)
        print(f"converted {svg.name} -> {pdf.name}")
    for dst_dir in (MANUSCRIPT,):
        dst = dst_dir / f"{stem}.pdf"
        if not dst.exists() or dst.stat().st_mtime < pdf.stat().st_mtime:
            shutil.copy2(pdf, dst)
            print(f"copied {pdf.name} -> {dst}")


def main() -> None:
    for stem in MANUSCRIPT_FIGURES:
        sync_pdf(stem)
    ga_pdf = FIG / "graphical_abstract.pdf"
    if ga_pdf.exists():
        shutil.copy2(ga_pdf, SUBMISSION / "graphical_abstract.pdf")
        print("copied graphical_abstract.pdf -> submission/")


if __name__ == "__main__":
    main()
