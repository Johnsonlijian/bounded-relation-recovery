"""R05 figures: identification gap and channel-selector dependence.

Sources are project CSVs already computed. SVG and PDF are both written.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
DATA = ROOT / "outputs"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 6.8,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})


def channel_controls_figure() -> None:
    """One figure, three channel-contract controls.

    The earlier split into two figures repeated the angle predicate panel in
    both, and the duplication made one caption describe a panel it did not
    contain. The angle panel now appears only once, in the angle figure that
    analyze_rebuild writes.
    """
    sig = pd.read_csv(DATA / "r04_rp2301_first_minimum.csv")
    loc = pd.read_csv(DATA / "r04_rp2301_local_mode_chunk_03.csv")
    rnd = pd.read_csv(DATA / "r05_rp2301_round_corner.csv")
    bend = pd.read_csv(DATA / "r05_rp2301_bending.csv")
    sig["err_eq"] = (sig["kw_first_min"] / sig["kw_equation19"] - 1).abs() * 100
    sig["err_k4"] = (sig["kw_first_min"] / 4.0 - 1).abs() * 100

    fig, axes = plt.subplots(1, 3, figsize=(5.43, 2.7))

    ax = axes[0]
    ax.axhspan(0.90, 1.10, color="#e7e5e4", zorder=0)
    ax.axhline(1.0, color="#44403c", lw=0.7)
    ax.scatter(sig["eta_w"], sig["ratio_first"], s=20, c="#1d4e89", zorder=3,
               label="sharp, signature min.")
    ax.scatter(rnd["eta_w"], rnd["ratio"], s=24, facecolors="none", edgecolors="#0f766e",
               linewidths=1.0, zorder=4, label="round corner, r=2.5t")
    ax.scatter(loc["eta_w"], loc["ratio_local"], s=24, marker="D", c="#9a3412", zorder=3,
               label="pure-local basis")
    ax.set_xlabel("web-to-flange ratio h/b", fontsize=6.8)
    ax.set_ylabel("FSM coefficient / Eq. 19", fontsize=6.8)
    ax.set_title("(a) Selector dependence", fontsize=7.2)
    ax.set_ylim(0.7, 1.5)
    ax.tick_params(labelsize=6.6)
    # Short labels only: longer wording overflowed the axes into panel (b).
    ax.legend(frameon=False, fontsize=6.0, loc="upper left", handletextpad=0.25,
              handlelength=1.4, borderpad=0.15, labelspacing=0.25)

    ax = axes[1]
    ax.scatter(sig["eta_w"], sig["err_eq"], s=18, c="#1d4e89", zorder=3, label="Eq. 19")
    ax.scatter(sig["eta_w"] + 0.15, sig["err_k4"], s=18, c="#9a3412", marker="s", zorder=3,
               label="element k = 4")
    ax.axhline(10, color="#a8a29e", lw=0.6, ls="--")
    ax.set_xlabel("web-to-flange ratio h/b", fontsize=6.8)
    ax.set_ylabel("absolute deviation from FSM (%)", fontsize=6.8)
    ax.set_title("(b) Against the element baseline", fontsize=7.2)
    ax.tick_params(labelsize=6.6)
    ax.legend(frameon=False, fontsize=6.4, loc="upper right", handletextpad=0.3,
              borderpad=0.15, labelspacing=0.25)
    ax.set_ylim(0, 58)

    ax = axes[2]
    ax.axhspan(0.90, 1.10, color="#e7e5e4", zorder=0)
    ax.axhline(1.0, color="#44403c", lw=0.6)
    ax.scatter(bend["eta_w"], bend["ratio"], s=24, c="#1d4e89", zorder=3)
    ax.set_xlabel("web-to-flange ratio h/b", fontsize=6.8)
    ax.set_ylabel("FSM / bending equation", fontsize=6.8)
    ax.set_title("(c) Major-axis bending", fontsize=7.2)
    ax.tick_params(labelsize=6.6)
    ax.set_ylim(0.75, 1.15)

    fig.tight_layout()
    fig.savefig(OUT / "figure9_two_relations.pdf")
    fig.savefig(OUT / "figure9_two_relations.svg")
    fig.savefig(OUT / "figure9_two_relations.png", dpi=300)
    plt.close()
    print("wrote figure9 (three channel controls)")


def graphical_abstract() -> None:
    """Elsevier-style graphical abstract (vector PDF/SVG)."""
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    boxes = [
        (0.4, 3.6, 2.0, 1.2, "#e7e5e4", "Legacy relation\n+ rounded table"),
        (3.0, 3.6, 2.2, 1.2, "#dbeafe", "Predicates +\ninterval evidence"),
        (5.8, 3.6, 1.6, 1.2, "#fef3c7", "One\naction"),
        (0.4, 1.2, 2.0, 1.2, "#fee2e2", "Reject\n(non-executable)"),
        (3.0, 1.2, 2.2, 1.2, "#dcfce7", "Bounded query\n(angle)"),
        (5.8, 1.2, 1.6, 1.2, "#ffedd5", "Withhold\n(channel)"),
    ]
    for x, y, w, h, color, label in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#44403c", lw=0.8))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.5)

    ax.annotate("", xy=(3.0, 4.2), xytext=(2.45, 4.2), arrowprops=dict(arrowstyle="->", lw=0.9))
    ax.annotate("", xy=(5.75, 4.2), xytext=(5.25, 4.2), arrowprops=dict(arrowstyle="->", lw=0.9))
    ax.annotate("", xy=(1.4, 3.55), xytext=(1.4, 2.45), arrowprops=dict(arrowstyle="->", lw=0.9, color="#9a3412"))
    ax.annotate("", xy=(4.1, 3.55), xytext=(4.1, 2.45), arrowprops=dict(arrowstyle="->", lw=0.9, color="#166534"))
    ax.annotate("", xy=(6.6, 3.55), xytext=(6.6, 2.45), arrowprops=dict(arrowstyle="->", lw=0.9, color="#c2410c"))

    ax.text(5.0, 0.35, "Cold-formed steel evidence programme", ha="center", fontsize=8, color="#57534e")
    fig.tight_layout()
    fig.savefig(OUT / "graphical_abstract.pdf")
    fig.savefig(OUT / "graphical_abstract.svg")
    fig.savefig(ROOT / "submission" / "graphical_abstract.pdf")
    fig.savefig(ROOT / "submission" / "graphical_abstract.svg")
    plt.close()
    print("wrote graphical_abstract")


def main() -> None:
    # The graphical abstract is owned by r06_fix_figures.py, which writes the
    # current 1.83:1 Elsevier layout. Rebuilding it here silently reverted it to
    # an older design, so this entry point no longer touches it.
    channel_controls_figure()


if __name__ == "__main__":
    main()
