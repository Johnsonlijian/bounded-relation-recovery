"""Figure for BRR case 3: the published Cc correlations against the displayed half-unit.

Encoding rule: colour carries the reduced action, not the author. The two correlations
that fail positivity on the observed domain are drawn in the reject hue and the seven
that miss the displayed interval in the retain hue, so the panel states the decision the
case actually produces. Author identity is carried by the dash pattern and the label.

The reject set is read from outputs/r07_compression_index_contract.json rather than being
hard-coded, so the figure cannot disagree with the evaluator.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"; MAN = ROOT / "manuscript"
plt.rcParams.update({"font.family": "serif", "font.size": 7.4, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

REL = [
    ("Sowers & Sowers 1970", 0.75, -0.375), ("Ahadiyan et al. 2008", -0.95, 1.02),
    ("Peck & Reed 1954", 0.208, 0.0083), ("Rendon-Herrero 1980", 0.49, -0.11),
    ("Park & Lee 2011", 0.287, -0.015), ("Gunduz & Arman 2007", 0.506, -0.11),
    ("Bowles 1989", 0.40, -0.10), ("Azzouz et al. 1976", 0.40, -0.25),
    ("Lav & Ansal 2001", 0.407, -0.094),
]


def name_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


contract = json.loads((ROOT / "outputs" / "r07_compression_index_contract.json").read_text(encoding="utf-8"))
rejected: set[str] = set()
for record in contract["results"]:
    rkey = name_key(str(record["relation"]))
    for name, _, _ in REL:
        k = name_key(name)
        if (rkey == k or rkey.startswith(k)) and str(record["action"]).startswith("REJECT"):
            rejected.add(name)
if len(rejected) != 2:
    raise SystemExit(f"expected two rejected correlations from the contract, got {sorted(rejected)}")
print("rejected by the evaluator:", sorted(rejected))

rows = [l.split(",") for l in (ROOT / "outputs" / "r07_compression_index_dataset.csv").read_text().strip().splitlines()[1:]]
e0 = np.array([float(r[0]) for r in rows]); cc = np.array([float(r[1]) for r in rows])
xs = np.linspace(0.45, 2.05, 400)

C_REJECT, C_RETAIN = "#C1440E", "#9C7A12"
REJ_STYLE = ["-", (0, (4.5, 1.6))]
RET_STYLE = ["-", (0, (5.5, 1.8)), (0, (1.2, 1.5)), (0, (6, 1.3, 1.3, 1.3)),
             (0, (2.2, 1.3)), (0, (7, 2)), (0, (1.2, 1.2, 4, 1.2))]

fig, ax = plt.subplots(figsize=(5.43, 3.2), dpi=220, constrained_layout=True)
ax.axhspan(-0.0005, 0.0005, color="#dcfce7", zorder=0)
ax.axhline(0, color="#a8a29e", lw=0.6, zorder=1)

ri = ti = 0
for name, m, b in REL:
    if name in rejected:
        ax.plot(xs, m * xs + b, lw=1.5, color=C_REJECT, ls=REJ_STYLE[ri],
                label=f"reject: {name}", zorder=2)
        ri += 1
    else:
        ax.plot(xs, m * xs + b, lw=0.9, color=C_RETAIN, ls=RET_STYLE[ti],
                label=f"retain: {name}", zorder=2)
        ti += 1
ax.scatter(e0, cc, s=3, color="#1c1917", alpha=0.45, zorder=3, label=f"measured ({len(e0)} cells)")

ax.set_xlim(0.45, 2.05); ax.set_ylim(-0.3, 1.4)
ax.set_xlabel("initial void ratio $e_0$", fontsize=7.6)
ax.set_ylabel("compression index $C_c$", fontsize=7.6)
ax.legend(frameon=False, fontsize=6.4, ncol=2, loc="upper left", handletextpad=0.35,
          columnspacing=0.7, borderpad=0.15, labelspacing=0.22)
ax.tick_params(labelsize=6.8)
ax.set_title("Nine published $e_0$-only correlations against 445 cells", fontsize=7.4)
for ext in ("pdf", "svg"):
    fig.savefig(OUT / f"figure11_geotechnical_case.{ext}", bbox_inches="tight")
    fig.savefig(MAN / f"figure11_geotechnical_case.{ext}", bbox_inches="tight")
plt.close(fig)
print("wrote figure11_geotechnical_case")
