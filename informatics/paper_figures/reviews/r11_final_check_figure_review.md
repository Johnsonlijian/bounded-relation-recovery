# Figure QA after the R11 final check

Scope: the five figures the manuscript actually includes. Each was inspected as a standalone
300–400 dpi render **and** at the size it occupies on the compiled page. Effective font size is
computed as `design pt x (LaTeX column width 391.4 pt / figure natural width)`.

| Manuscript figure | Source stem | Natural width | LaTeX scale | Smallest effective text | Verdict |
|---|---|---|---|---|---|
| Figure 1 | `figure12_bounded_release_calculus` | 391.0 pt | 1.00 | 6.8 pt | PASS |
| Figure 2 | `figure13_scale_nonidentification` | 391.0 pt | 1.00 | 6.8 pt | PASS |
| Figure 3 | `figure2_admissibility_and_replay` | 399.4 pt | 0.98 | 6.5 pt | PASS |
| Figure 4 | `figure9_two_relations` | 391.0 pt | 1.00 | 6.2 pt | PASS (lowest label is the panel-a legend) |
| Figure 5 | `figure11_geotechnical_case` | 399.4 pt | 0.98 | 6.5 pt | PASS |

All five masters shipped in the submission package are byte-comparable (identical page size) with
the figures embedded in `manuscript/main.pdf`.

## Defects found and repaired in this round

### F1 — Figure 1 panel A: the blocker rows were invisible (REBUILD)
`r10_super_uplift_evidence.py` drew `barh(width = expected_order)`, i.e. bar **length** encoded the
action level on a categorical axis. `REJECT` has level 0, so all three blocker rows
(`mechanics.positivity`, `mechanics.finiteness`, `provenance.source_verified`) rendered as
zero-length bars. The panel therefore omitted exactly the failure path the paper is about.
Repaired by encoding the action as a categorical block at the resolved level, so every row shows a
visible mark, and by relabelling the control row.

### F2 — Figure 1 panel B: annotation collided with the value label and the panel title (REVISION)
The note "same Zhang source; not independent validation" was placed at `(0.02, 0.95)` in axes
coordinates with no headroom, so it overlapped the `0.739` value label and the panel title.
Repaired with explicit `ylim` headroom and a re-anchored, shortened note.

### F3 — Figure 2: the intervals the panel claims to show were not resolvable (REBUILD)
The four groupwise scale intervals are ~0.005 MPa wide on a ~190 MPa axis, so a length encoding
collapsed them to sub-pixel hairlines; the reader could see only the two global vertical lines.
Rebuilt as a two-panel figure: panel A places the intervals on a logarithmic axis with their numeric
bounds annotated and shades the empty common-scale band; panel B plots the four interval widths,
all of which are positive. The defensive title "Global scale infeasibility is a result, not a
disclaimer" was replaced by the scientific statement "the four groupwise intervals do not overlap".

### F4 — Figure 4: caption described one panel of a two-panel figure, and duplicated Figure 3 (REBUILD)
`figure9_two_relations` contained a left panel showing the angle predicate (already Figure 3a) and a
right panel showing the channel selectors, while the caption described only the channel content.
The angle panel also reappeared inside `figure10_argument`. The channel figure was rebuilt as three
panels (selector dependence / element baseline / major-axis bending) and `figure10_argument` was
withdrawn, removing the triplicated angle plot.

### F5 — Presentation-layer scaling: three figures printed below 5 pt (REBUILD)
`figure2`, `figure9` and `figure11` were drawn on 7.4-inch canvases that the LaTeX column scales by
~0.49–0.72, leaving the smallest labels at 4.2–4.5 pt. All three were redrawn on a canvas matched to
the 391.4 pt column at 6.5–7.6 pt design sizes.

### F6 — Figure-master/PDF divergence (PACKAGE)
`figures/figure2_admissibility_and_replay.pdf` was a stale October-3 variant (a group-mean bar
chart) while `manuscript/figure2...pdf` held the October-6 cell-level scatter that the caption and
body text describe; the package shipped the stale master. Separately, after the R11 figure rebuild,
`manuscript/figure9_two_relations.pdf` was a stale two-panel copy. Both were synchronised, and
`src/r06_export_figure_pdfs.py` now refuses to copy a master whose page width disagrees with the
manuscript copy instead of silently overwriting by mtime.

## Checks performed with no defect found

- No text/text, text/marker or text/spine overlap in any of the five figures at print size.
- No clipped text or mark at the axes frame or page boundary (verified after the canvas changes).
- Every axis carries a unit or a categorical label; every legend is inside a free region.
- Figure/table citation order is ascending (Figures 1–5 cited at source lines 162, 203, 225, 240,
  254); no orphan float, no float without an asset.
- Panel counts match caption panel letters for all five figures.
- All masters are vector PDF with an editable SVG and a PNG preview at 300 dpi.
