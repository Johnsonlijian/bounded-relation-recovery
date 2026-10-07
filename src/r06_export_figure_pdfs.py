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
    """Convert a missing PDF from its SVG, and mirror it into manuscript/.

    Guard: a master is copied only when the two copies agree on page size. A pure
    mtime test pushed a stale, wider master over a newer manuscript copy and left
    the compiled PDF and the shipped figure master describing different figures.
    """
    svg = FIG / f"{stem}.svg"
    if not svg.exists():
        svg = MANUSCRIPT / f"{stem}.svg"
    pdf = FIG / f"{stem}.pdf"
    if not pdf.exists():
        if not svg.exists():
            raise FileNotFoundError(f"missing SVG/PDF for {stem}")
        svg_to_pdf(svg, pdf)
        print(f"converted {svg.name} -> {pdf.name}")

    def page_width(path: Path) -> float | None:
        try:
            import re
            import subprocess

            out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
            m = re.search(r"Page size:\s+([0-9.]+)\s+x", out)
            return float(m.group(1)) if m else None
        except Exception:
            return None

    dst = MANUSCRIPT / f"{stem}.pdf"
    if not dst.exists():
        shutil.copy2(pdf, dst)
        print(f"copied {pdf.name} -> {dst}")
        return
    w_src, w_dst = page_width(pdf), page_width(dst)
    if w_src is None or w_dst is None:
        print(f"SKIP {stem}: page size unavailable, not overwriting")
        return
    if abs(w_src - w_dst) > 0.5:
        raise SystemExit(
            f"PARITY ERROR {stem}: figures/{stem}.pdf is {w_src} pt wide but "
            f"manuscript/{stem}.pdf is {w_dst} pt. Regenerate the figure from its "
            f"generator instead of copying; do not overwrite the manuscript copy."
        )
    if dst.stat().st_mtime < pdf.stat().st_mtime:
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
