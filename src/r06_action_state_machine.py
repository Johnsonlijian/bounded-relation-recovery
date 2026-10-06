"""Figure: protocol action state machine (informatics artefact).

Outputs vector PDF/SVG under figures/ and manuscript/.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

BOX = dict(boxstyle="round,pad=0.35,rounding_size=0.08", linewidth=0.8)


def _box(ax, xy, text, facecolor, width=2.15, height=0.72):
    x, y = xy
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle=BOX["boxstyle"],
        linewidth=BOX["linewidth"],
        edgecolor="#44403c",
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=8.2)
    return (x, y, width, height)


def _arrow(ax, p0, p1, text=None, color="#57534e"):
    arr = FancyArrowPatch(
        p0,
        p1,
        arrowstyle="-|>",
        mutation_scale=10,
        linewidth=0.9,
        color=color,
        shrinkA=4,
        shrinkB=4,
    )
    ax.add_patch(arr)
    if text:
        mx = (p0[0] + p1[0]) / 2
        my = (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.12, text, ha="center", va="bottom", fontsize=7.2, color=color)


def main() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    start = _box(ax, (1.2, 5.2), "Typed run\nobject + relation", "#f5f5f4", width=1.9, height=0.78)
    mech = _box(ax, (3.4, 5.2), "Mechanics predicates\npositivity / trend / finite", "#dbeafe")
    reject = _box(ax, (7.8, 5.2), "reject\nnon-executable", "#fee2e2")
    evid = _box(ax, (3.4, 3.55), "Evidence predicates\ninterval + coverage", "#e0f2fe")
    retain = _box(ax, (7.8, 3.55), "retain\nbounded claim", "#ffedd5")
    prov = _box(ax, (3.4, 1.95), "Provenance contract\nsource + selector named", "#ede9fe")
    query = _box(ax, (7.8, 1.95), "allow\nbounded query", "#dcfce7")
    ops = _box(ax, (3.4, 0.45), "Operational gates\n(source rerun + human review)", "#f5f5f4", width=2.35, height=0.78)
    blocked = _box(ax, (7.8, 0.45), "operational use\nnot granted here", "#e7e5e4")

    _arrow(ax, (start[0] + start[2] / 2, start[1]), (mech[0] - mech[2] / 2, mech[1]))
    _arrow(ax, (mech[0] + mech[2] / 2, mech[1]), (reject[0] - reject[2] / 2, reject[1]), "fail")
    _arrow(ax, (mech[0], mech[1] - mech[3] / 2), (evid[0], evid[1] + evid[3] / 2), "pass")
    _arrow(ax, (evid[0] + evid[2] / 2, evid[1]), (retain[0] - retain[2] / 2, retain[1]), "fail / open")
    _arrow(ax, (evid[0], evid[1] - evid[3] / 2), (prov[0], prov[1] + prov[3] / 2), "pass")
    _arrow(ax, (prov[0] + prov[2] / 2, prov[1]), (query[0] - query[2] / 2, query[1]), "complete")
    _arrow(ax, (prov[0], prov[1] - prov[3] / 2), (retain[0], retain[1] - retain[3] / 2), "selector mismatch")
    _arrow(ax, (query[0], query[1] - query[3] / 2), (ops[0], ops[1] + ops[3] / 2))
    _arrow(ax, (ops[0] + ops[2] / 2, ops[1]), (blocked[0] - blocked[2] / 2, blocked[1]), "open")

    ax.text(
        0.35,
        0.2,
        "One auditable action per run. Fitting is not a transition.",
        fontsize=8,
        color="#57534e",
    )

    fig.tight_layout()
    for stem in ("figure_action_state_machine",):
        fig.savefig(OUT / f"{stem}.pdf")
        fig.savefig(OUT / f"{stem}.svg")
        fig.savefig(ROOT / "manuscript" / f"{stem}.pdf")
        fig.savefig(ROOT / "manuscript" / f"{stem}.svg")
    plt.close()
    print("wrote figure_action_state_machine")


if __name__ == "__main__":
    main()
