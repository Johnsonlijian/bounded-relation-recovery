"""R06 figure corrections.

Three defects fixed here, all found by rendered inspection plus data reconciliation:

1. ``figure2_admissibility_and_replay`` panel (b) plotted the *mean of per-group* replay
   RMSE (0.710 / 0.340) while its caption and the body text describe the *cell-level*
   replay error (0.923 / 0.354) with a 5 % screen line that the panel did not draw.
   Panel (b) is rebuilt from the per-cell tables, and now shows both evidence routes.

2. ``figure_action_state_machine`` printed its footnote inside the "Operational gates"
   box, and its mechanics box implied that any mechanics-predicate failure rejects, which
   ``src/brr/actions.py`` does not do (a trend failure demotes, it does not reject).

3. ``graphical_abstract`` was 396 x 216 pt (1.83:1) with three arrows pointing from the
   outcomes back into the contract, which reads as if the action feeds the evidence.  It
   is redrawn at 13.0 x 5.2 cm (2.50:1, Elsevier's minimum aspect) with a single
   contract -> one-action topology.

Vector PDF and SVG are written to ``figures/``; the two manuscript figures are mirrored
into ``manuscript/``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
MAN = ROOT / "manuscript"
SUB = ROOT / "submission"
DATA = ROOT / "outputs"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

SCREEN_PCT = 5.0
C_PRINT, C_REC = "#9a3412", "#1d4e89"
C_REPLAY, C_REBUILD = "#5E4FA2", "#2A9D8F"


def _save(fig, stem: str, also_manuscript: bool = False, also_submission: bool = False) -> None:
    # The graphical abstract must keep its exact 13.0 x 5.2 cm canvas (Elsevier wants
    # 531 x 1328 px h x w at 96 dpi, i.e. ratio 2.50), so it is never cropped to content.
    tight = stem != "graphical_abstract"
    kw = {"bbox_inches": "tight"} if tight else {}
    for ext in ("pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", **kw)
        if also_manuscript:
            fig.savefig(MAN / f"{stem}.{ext}", **kw)
        if also_submission:
            fig.savefig(SUB / f"{stem}.{ext}", **kw)
    if stem == "graphical_abstract":
        fig.savefig(OUT / f"{stem}.png", dpi=300, **kw)
        fig.savefig(SUB / f"{stem}.png", dpi=300, **kw)
    plt.close(fig)
    print(f"wrote {stem}")


# --------------------------------------------------------------------------------------
# 1. admissibility + replay
# --------------------------------------------------------------------------------------


def figure_admissibility() -> None:
    replay = pd.read_csv(DATA / "full_cufsm_replay_recomputed.csv")
    rebuild = pd.read_csv(DATA / "r03_zhang_model_reconstruction.csv")

    replay = replay.rename(columns={"reconstructed_relative_error_pct": "err"})
    rebuild = rebuild.rename(columns={"relative_error_pct": "err"})

    fig, axes = plt.subplots(1, 2, figsize=(5.43, 2.55), dpi=220, constrained_layout=True)

    # ---- panel (a): mechanics admissibility -----------------------------------------
    ax = axes[0]
    x = np.linspace(1.1, 1.5, 400)
    q_printed = lambda t: 0.292 - 1.060 * t**2 + 0.339 * t
    q_recovered = lambda t: 0.292 - 0.339 * t**2 + 1.060 * t
    ax.axhline(0, color="#a8a29e", lw=0.7)
    ax.plot(x, q_printed(x), color=C_PRINT, lw=1.4, label="printed expression")
    ax.plot(x, q_recovered(x), color=C_REC, lw=1.4, label="recovered assignment")
    ax.fill_between(x, q_printed(x), 0, where=q_printed(x) < 0, color="#fecaca", alpha=0.5, lw=0)
    ax.annotate(f"{q_printed(1.1):.3f}", xy=(1.10, q_printed(1.1)), xytext=(1.13, -0.30),
                fontsize=6.6, color=C_PRINT,
                arrowprops=dict(arrowstyle="-", color=C_PRINT, lw=0.5))
    ax.annotate(f"{q_printed(1.5):.3f}", xy=(1.50, q_printed(1.5)), xytext=(1.30, -0.62),
                fontsize=6.6, color=C_PRINT,
                arrowprops=dict(arrowstyle="-", color=C_PRINT, lw=0.5))
    ax.set_xlim(1.1, 1.5)
    ax.set_ylim(-1.75, 1.35)
    ax.set_xlabel("limb ratio $x=a/b$", fontsize=6.8)
    ax.set_ylabel("shape $q(x)$", fontsize=6.8)
    ax.set_title("(a) mechanics admissibility", fontsize=7.2)
    # Legend sits in the empty band between the zero line and the recovered curve; at
    # the lower left the printed curve ran straight through the label text.
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.02, 0.87), fontsize=6.8)
    ax.tick_params(labelsize=6.8)

    # ---- panel (b): the 630-cell check, both routes ----------------------------------
    ax = axes[1]
    ax.axhspan(-SCREEN_PCT, SCREEN_PCT, color="#e7e5e4", zorder=0)
    for y in (SCREEN_PCT, -SCREEN_PCT):
        ax.axhline(y, color="#78716c", lw=0.8, ls="--", zorder=1)
    ax.axhline(0, color="#a8a29e", lw=0.6, zorder=1)
    rng = np.random.default_rng(20261006)
    ax.scatter(replay["a_over_b"] + rng.uniform(-0.012, 0.012, len(replay)), replay["err"],
               s=3.5, marker="o", linewidths=0,
               color=C_REPLAY, alpha=0.55, zorder=2,
               label="table replay (0.923 / 0.354 %)")
    ax.scatter(rebuild["a_over_b"] + rng.uniform(-0.012, 0.012, len(rebuild)), rebuild["err"],
               s=3.5, marker="s", linewidths=0,
               color=C_REBUILD, alpha=0.55, zorder=3,
               label="geometry rebuild (0.532 %)")
    ax.set_xlim(1.04, 1.56)
    # Headroom above and below the 5 % screen lines: the legend and the screen note used
    # to be struck through by the dashed lines themselves.
    ax.set_ylim(-SCREEN_PCT - 2.6, SCREEN_PCT + 2.6)
    ax.set_xlabel("limb ratio $x=a/b$", fontsize=6.8)
    ax.set_ylabel("relative error (%)", fontsize=6.8)
    ax.set_title("(b) held-out 630-cell check", fontsize=7.2)
    ax.text(0.985, 0.03, "dashed: 5 % screen", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6.6, color="#57534e")
    ax.legend(frameon=False, loc="upper right", fontsize=6.6, handletextpad=0.3, borderpad=0.1)
    ax.tick_params(labelsize=6.8)

    _save(fig, "figure2_admissibility_and_replay", also_manuscript=True)


# --------------------------------------------------------------------------------------
# 2. action state machine
# --------------------------------------------------------------------------------------

BOX = dict(boxstyle="round,pad=0.32,rounding_size=0.08", linewidth=0.8)


def _box(ax, xy, text, facecolor, width=2.15, height=0.74, fontsize=8.2):
    bx, by = xy
    ax.add_patch(FancyBboxPatch((bx - width / 2, by - height / 2), width, height,
                                boxstyle=BOX["boxstyle"], linewidth=BOX["linewidth"],
                                edgecolor="#44403c", facecolor=facecolor))
    ax.text(bx, by, text, ha="center", va="center", fontsize=fontsize)
    return (bx, by, width, height)


def _arrow(ax, p0, p1, text=None, color="#57534e", dx=0.0, dy=0.11):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10,
                                 linewidth=0.9, color=color, shrinkA=4, shrinkB=4))
    if text:
        ax.text((p0[0] + p1[0]) / 2 + dx, (p0[1] + p1[1]) / 2 + dy, text,
                ha="center", va="bottom", fontsize=5.9, color=color)


def figure_state_machine() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.set_xlim(-0.5, 10.8)
    ax.set_ylim(-0.55, 6.25)
    ax.axis("off")

    start = _box(ax, (1.15, 5.35), "Typed run\nobject + relation", "#f5f5f4", 1.95, 0.8)
    mech = _box(ax, (3.95, 5.35), "Mechanics predicates\npositivity / finiteness / trend", "#dbeafe")
    reject = _box(ax, (8.6, 5.35), "reject\nnon-executable", "#fee2e2")
    evid = _box(ax, (3.95, 3.75), "Evidence predicates\ninterval (Eq. 1) + coverage", "#e0f2fe")
    retain = _box(ax, (8.6, 3.75), "retain\nbounded claim", "#ffedd5")
    prov = _box(ax, (3.95, 2.15), "Provenance contract\nsource + selector named", "#ede9fe")
    query = _box(ax, (8.6, 2.15), "allow\nbounded query", "#dcfce7")
    ops = _box(ax, (3.95, 0.5), "Operational gates\nindependent source rerun\n+ human review", "#f5f5f4",
               2.6, 1.0, fontsize=7.6)
    blocked = _box(ax, (8.6, 0.5), "operational use\nnot granted here", "#e7e5e4")

    _arrow(ax, (start[0] + start[2] / 2, start[1]), (mech[0] - mech[2] / 2, mech[1]))
    _arrow(ax, (mech[0] + mech[2] / 2, mech[1]), (reject[0] - reject[2] / 2, reject[1]),
           "fail", dy=0.03)
    _arrow(ax, (mech[0], mech[1] - mech[3] / 2), (evid[0], evid[1] + evid[3] / 2))
    ax.text(mech[0] + 0.10, (mech[1] - mech[3] / 2 + evid[1] + evid[3] / 2) / 2, "pass",
            ha="left", va="center", fontsize=6.2, color="#57534e")
    _arrow(ax, (evid[0] + evid[2] / 2, evid[1]), (retain[0] - retain[2] / 2, retain[1]),
           "fail / open", dy=0.03)
    _arrow(ax, (evid[0], evid[1] - evid[3] / 2), (prov[0], prov[1] + prov[3] / 2))
    ax.text(evid[0] + 0.10, (evid[1] - evid[3] / 2 + prov[1] + prov[3] / 2) / 2, "pass",
            ha="left", va="center", fontsize=6.2, color="#57534e")
    _arrow(ax, (prov[0] + prov[2] / 2, prov[1]), (query[0] - query[2] / 2, query[1]), "complete")
    _arrow(ax, (prov[0] - prov[2] / 2, prov[1] + 0.18), (retain[0] - retain[2] / 2, retain[1] - 0.18),
           "selector mismatch", dx=0.0, dy=0.06)
    _arrow(ax, (query[0], query[1] - query[3] / 2), (ops[0] + ops[2] / 2, ops[1] + 0.28))
    _arrow(ax, (ops[0] + ops[2] / 2, ops[1] - 0.28), (blocked[0] - blocked[2] / 2, blocked[1]),
           "open")

    ax.text(0.05, -0.42,
            "One auditable action per run; actions are monotone-blocking. Fitting is not a transition.\n"
            "A failed trend predicate demotes to $\\it{retain}$; only positivity, finiteness or provenance failure rejects.",
            fontsize=6.9, color="#57534e", va="top")

    _save(fig, "figure_action_state_machine", also_manuscript=True)


# --------------------------------------------------------------------------------------
# 3. graphical abstract, Elsevier geometry (13.0 x 5.2 cm -> 2.50:1)
# --------------------------------------------------------------------------------------


def graphical_abstract() -> None:
    cm = 1 / 2.54
    fig = plt.figure(figsize=(13.0 * cm, 5.2 * cm), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")

    def box(x, y, w, h, title, body, fc, ec="#44403c", ts=5.4, bs=4.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.6,rounding_size=0.8",
                                    linewidth=0.7, edgecolor=ec, facecolor=fc))
        ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="center",
                fontsize=ts, fontweight="bold", color="#1c1917")
        ax.text(x + w / 2, y + h / 2 - 1.6, body, ha="center", va="center",
                fontsize=bs, color="#292524", linespacing=1.45)

    def arrow(x0, y0, x1, y1, color="#57534e"):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                     mutation_scale=5, linewidth=0.7, color=color,
                                     shrinkA=1, shrinkB=1))

    ax.text(50, 38.2, "One typed contract, one auditable action per relation",
            ha="center", va="center", fontsize=6.6, fontweight="bold", color="#1c1917")
    ax.text(50, 35.3,
            "A published relation is executable only if its mechanics predicates, rounded evidence and provenance survive the same contract.",
            ha="center", va="center", fontsize=4.6, color="#57534e")

    # input
    box(1.5, 11.0, 21.0, 19.5, "Published relation\n+ rounded table",
        "printed expression\nand its displayed cells\n\n2 relations\n630 + 20 + 21 cells",
        "#f5f5f4", bs=4.4)

    # contract
    box(26.0, 8.0, 31.0, 25.5, "Typed contract",
        "object · state · response\nrelation · predicate\nevidence · provenance\n\n"
        "1  mechanics: positivity,\n    finiteness, trend\n"
        "2  evidence: Eq. 1 interval\n    feasibility, coverage\n"
        "3  provenance: source and\n    selector named\n\n"
        "fixed order · monotone blocking",
        "#dbeafe", bs=4.3)

    # outcomes
    box(60.5, 25.4, 38.0, 8.1, "reject, non-executable",
        "printed angle expression is negative on\nits declared domain; no fit is computed",
        "#fee2e2", bs=4.3)
    box(60.5, 16.0, 38.0, 8.1, "allow a bounded query",
        "one of 48 printed-magnitude assignments\npasses; 630 published cells, 5 % screen",
        "#dcfce7", bs=4.3)
    box(60.5, 6.6, 38.0, 8.1, "retain a bounded claim",
        "channel equation passes, but an unreproduced\nselector moves the sample 14.8 % low to 33 % high",
        "#ffedd5", bs=4.3)

    arrow(22.8, 20.8, 25.7, 20.8)
    for y in (29.4, 20.0, 10.6):
        arrow(57.3, 20.8, 60.2, y)

    ax.text(50, 1.6,
            "Exactly one action is emitted per run; the action is a protocol output, not a fit. "
            "Operational design use is a further human gate and is not granted here.",
            ha="center", va="center", fontsize=4.2, color="#57534e")

    _save(fig, "graphical_abstract")
    fig2 = plt.gcf()


def main() -> None:
    figure_admissibility()
    figure_state_machine()
    graphical_abstract()


if __name__ == "__main__":
    main()
