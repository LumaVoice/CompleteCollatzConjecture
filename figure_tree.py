#!/usr/bin/env python3
# ================================================================
#  Inverse-Tree Visualization for Wall and Bridge Collatz Types
#  Author : Ryosuke Miyazawa
#  License: MIT
#
#  Related DOI:
#    - The Shadow Collatz Conjecture: The Journey of All Integers Toward −1
#      https://doi.org/10.5281/zenodo.16754304
#    - A Complete Extension of Collatz Dynamics to All Integers via the Odd-Zero Paradigm
#      https://doi.org/10.5281/zenodo.16783743
#
#  DESCRIPTION:
#    Generates PDF vector graphics for:
#      - Signed log₂ inverse trees (B(+1), B(-1), W(+1), W(-1))
#      - Branching window diagrams (number line ±60, mod 6 ≡ ±2 ticks)
#      - Coverage curves for B(+1) inverse BFS (no pruning)
#
#  USAGE:
#    $ python3 figure_tree.py
#    (Outputs PDFs and CSV in current directory)
#
#  NOTES:
#    - Requires matplotlib
#    - No external data or internet required
#    - All figures are suitable for direct LaTeX inclusion
# ===============================================================

# -*- coding: utf-8 -*-
"""
Figures for: Inverse-Tree Formulation via Bridge B(±1)
Generates PDFs:
  1) signedlog_Bplus1_with_edges.pdf
  2) signedlog_Bplus1_Bminus1_with_edges.pdf
  3) signedlog_Wplus1_Wminus1_with_edges.pdf
  4) branch_window_combined_dualticks_d8.pdf
  5) bplus1_coverage_curves.pdf
  6) bplus1_coverage_unpruned_multiA.csv   (data for (5))

Dependencies: matplotlib (no seaborn). Python 3.9+ recommended.
"""

import math
from collections import deque
import csv
import matplotlib.pyplot as plt

# --------------------------- Colors ---------------------------
CYAN    = "#22a7f0"   # for B(+1)
MAGENTA = "#d24dff"   # for B(-1)
GRAY    = "#666666"

# --------------------------- Dynamics -------------------------
def preimages_B(y: int, s: int, odd_zero=True):
    """Bridge B(s): even -> divide by -2; odd -> 3n+s; s ∈ {+1,-1}."""
    yield -2 * y                            # even preimage (always)
    if (y - (-2 * s)) % 6 == 0:             # odd preimage condition
        yield (y - s) // 3
    if odd_zero and y == s:                 # Odd-Zero convention
        yield 0

def preimages_W(y: int, s: int, odd_zero=True):
    """Wall W(s): even -> divide by +2; odd -> 3n+s."""
    yield 2 * y
    if (y - (-2 * s)) % 6 == 0:
        yield (y - s) // 3
    if odd_zero and y == s:
        yield 0

def bfs_inverse_levels(s: int, depth: int, op="B"):
    """Unpruned BFS to given inverse depth. Returns list of levels (values), and map coords."""
    levels = [[] for _ in range(depth + 1)]
    seen = set([s])
    q = deque([(s, 0)])
    levels[0].append(s)
    pre = preimages_B if op == "B" else preimages_W
    while q:
        y, d = q.popleft()
        if d >= depth:
            continue
        for n in pre(y, s, odd_zero=True):
            if n in seen:
                continue
            seen.add(n)
            levels[d + 1].append(n)
            q.append((n, d + 1))
    for d in range(len(levels)):
        levels[d].sort()
    return levels, seen

def edges_from_levels(levels, s, op="B"):
    """Compute child->parent edges matching one forward step."""
    level_sets = [set(lv) for lv in levels]
    edges = []
    for d in range(1, len(levels)):
        for v in levels[d]:
            if v % 2 == 0:
                parent = (v // -2) if op == "B" else (v // 2)
            else:
                parent = 3 * v + s
            if parent in level_sets[d - 1]:
                edges.append((v, parent))
    return edges

# ----------------------- Coordinates --------------------------
def x_signed_log2(n: int) -> float:
    """x = sgn(n)*log2(1+|n|); x(0)=0."""
    if n == 0:
        return 0.0
    return math.copysign(math.log2(1 + abs(n)), n)

def coords_signed_log2(levels):
    coords = {}
    for d, nodes in enumerate(levels):
        for v in nodes:
            coords[v] = (x_signed_log2(v), d + 1)  # ground=0, root=1
    return coords

def coords_numberline(levels):
    coords = {}
    for d, nodes in enumerate(levels):
        for v in nodes:
            coords[v] = (float(v), d + 1)
    return coords

# ------------------------- Plotters ---------------------------
def plot_signedlog_single_Bplus1(depth=10, xlim=12.0, node_size=14, edge_w=0.6, out="signedlog_Bplus1_with_edges.pdf"):
    levels, _ = bfs_inverse_levels(+1, depth, op="B")
    edges = edges_from_levels(levels, +1, op="B")
    C = coords_signed_log2(levels)

    plt.figure(figsize=(11, 7))
    plt.axhline(0, linewidth=1.0, color="k")

    # ground shadows
    xs_ground = [x for (x, y) in C.values() if -xlim <= x <= xlim]
    plt.scatter(xs_ground, [0] * len(xs_ground), s=node_size * 0.6, color=CYAN, alpha=0.9, label="B(+1) shadows")

    # edges & nodes (crop by xlim for display only)
    for a, b in edges:
        xa, ya = C[a]; xb, yb = C[b]
        if -xlim <= xa <= xlim and -xlim <= xb <= xlim:
            plt.plot([xa, xb], [ya, yb], linewidth=edge_w, color=CYAN, alpha=0.75)
    xs = [C[v][0] for v in C if -xlim <= C[v][0] <= xlim]
    ys = [C[v][1] for v in C if -xlim <= C[v][0] <= xlim]
    plt.scatter(xs, ys, s=node_size, color=CYAN, alpha=0.95, label="B(+1) canopy")

    plt.xlabel(r"$x=\mathrm{sgn}(n)\,\log_2(1+|n|)$")
    plt.ylabel("inverse depth (ground=0, root=1)")
    plt.ylim(-0.5, depth + 1.5)
    plt.xlim(-xlim, xlim)
    plt.title(f"Inverse tree B(+1) with edges and ground shadows (depth ≤ {depth})")
    plt.legend(loc="upper right", frameon=False)
    plt.tight_layout(); plt.savefig(out, format="pdf"); plt.close()

def plot_signedlog_combined_Bpm1(depth=10, xlim=12.0, node_size=14, edge_w=0.6, out="signedlog_Bplus1_Bminus1_with_edges.pdf"):
    Lp, _ = bfs_inverse_levels(+1, depth, op="B")
    Lm, _ = bfs_inverse_levels(-1, depth, op="B")
    Ep = edges_from_levels(Lp, +1, op="B")
    Em = edges_from_levels(Lm, -1, op="B")
    Cp = coords_signed_log2(Lp)
    Cm = coords_signed_log2(Lm)

    plt.figure(figsize=(11, 7))
    plt.axhline(0, linewidth=1.0, color="k")

    # shadows
    xs_p_ground = [x for (x, y) in Cp.values() if -xlim <= x <= xlim]
    xs_m_ground = [x for (x, y) in Cm.values() if -xlim <= x <= xlim]
    plt.scatter(xs_p_ground, [0] * len(xs_p_ground), s=node_size * 0.6, color=CYAN, alpha=1.0, label="B(+1) shadows")
    plt.scatter(xs_m_ground, [0] * len(xs_m_ground), s=node_size * 0.6, color=MAGENTA, alpha=1.0, label="B(-1) shadows")

    # edges
    for a, b in Ep:
        xa, ya = Cp[a]; xb, yb = Cp[b]
        if -xlim <= xa <= xlim and -xlim <= xb <= xlim:
            plt.plot([xa, xb], [ya, yb], linewidth=edge_w, color=CYAN, alpha=0.75)
    for a, b in Em:
        xa, ya = Cm[a]; xb, yb = Cm[b]
        if -xlim <= xa <= xlim and -xlim <= xb <= xlim:
            plt.plot([xa, xb], [ya, yb], linewidth=edge_w, color=MAGENTA, alpha=0.75)

    # nodes
    xs_p = [Cp[v][0] for v in Cp if -xlim <= Cp[v][0] <= xlim]
    ys_p = [Cp[v][1] for v in Cp if -xlim <= Cp[v][0] <= xlim]
    xs_m = [Cm[v][0] for v in Cm if -xlim <= Cm[v][0] <= xlim]
    ys_m = [Cm[v][1] for v in Cm if -xlim <= Cm[v][0] <= xlim]
    plt.scatter(xs_p, ys_p, s=node_size, color=CYAN, alpha=0.95, label="B(+1) canopy")
    plt.scatter(xs_m, ys_m, s=node_size, color=MAGENTA, alpha=0.95, label="B(-1) canopy")

    plt.xlabel(r"$x=\mathrm{sgn}(n)\,\log_2(1+|n|)$")
    plt.ylabel("inverse depth (ground=0, root=1)")
    plt.ylim(-0.5, depth + 1.5)
    plt.xlim(-xlim, xlim)
    plt.title(f"Inverse trees B(+1) and B(-1) with edges and ground shadows (depth ≤ {depth})")
    plt.legend(loc="upper right", frameon=False)
    plt.tight_layout(); plt.savefig(out, format="pdf"); plt.close()

def plot_signedlog_combined_Wpm1(depth=10, xlim=12.0, node_size=14, edge_w=0.6, out="signedlog_Wplus1_Wminus1_with_edges.pdf"):
    Lp, _ = bfs_inverse_levels(+1, depth, op="W")
    Lm, _ = bfs_inverse_levels(-1, depth, op="W")
    Ep = edges_from_levels(Lp, +1, op="W")
    Em = edges_from_levels(Lm, -1, op="W")
    Cp = coords_signed_log2(Lp)
    Cm = coords_signed_log2(Lm)

    plt.figure(figsize=(11, 7))
    plt.axhline(0, linewidth=1.0, color="k")

    for a, b in Ep:
        xa, ya = Cp[a]; xb, yb = Cp[b]
        if -xlim <= xa <= xlim and -xlim <= xb <= xlim:
            plt.plot([xa, xb], [ya, yb], linewidth=edge_w, color=CYAN, alpha=0.75)
    for a, b in Em:
        xa, ya = Cm[a]; xb, yb = Cm[b]
        if -xlim <= xa <= xlim and -xlim <= xb <= xlim:
            plt.plot([xa, xb], [ya, yb], linewidth=edge_w, color=MAGENTA, alpha=0.75)

    xs_p = [Cp[v][0] for v in Cp if -xlim <= Cp[v][0] <= xlim]
    ys_p = [Cp[v][1] for v in Cp if -xlim <= Cp[v][0] <= xlim]
    xs_m = [Cm[v][0] for v in Cm if -xlim <= Cm[v][0] <= xlim]
    ys_m = [Cm[v][1] for v in Cm if -xlim <= Cm[v][0] <= xlim]
    plt.scatter(xs_p, ys_p, s=node_size, color=CYAN, alpha=0.95, label="W(+1) canopy")
    plt.scatter(xs_m, ys_m, s=node_size, color=MAGENTA, alpha=0.95, label="W(-1) canopy")

    plt.xlabel(r"$x=\mathrm{sgn}(n)\,\log_2(1+|n|)$")
    plt.ylabel("inverse depth (ground=0, root=1)")
    plt.ylim(-0.5, depth + 1.5)
    plt.xlim(-xlim, xlim)
    plt.title(f"Inverse trees W(+1) and W(-1) with edges (depth ≤ {depth})")
    plt.legend(loc="upper right", frameon=False)
    plt.tight_layout(); plt.savefig(out, format="pdf"); plt.close()

def plot_branch_window_combined_dualticks(depth=8, xwin=60, out="branch_window_combined_dualticks_d8.pdf"):
    """Number line window ±xwin, full tree drawn then crop; dual tick rulers (top=B+1≡-2, bottom=B-1≡+2)."""
    Lp, _ = bfs_inverse_levels(+1, depth, op="B")
    Lm, _ = bfs_inverse_levels(-1, depth, op="B")
    Ep = edges_from_levels(Lp, +1, op="B"); Cp = coords_numberline(Lp)
    Em = edges_from_levels(Lm, -1, op="B"); Cm = coords_numberline(Lm)

    fig, ax = plt.subplots(figsize=(10, 5.5))

    # full edges + nodes, then crop
    for a, b in Ep:
        xa, ya = Cp[a]; xb, yb = Cp[b]
        ax.plot([xa, xb], [ya, yb], linewidth=0.85, color=CYAN, alpha=0.8)
    for a, b in Em:
        xa, ya = Cm[a]; xb, yb = Cm[b]
        ax.plot([xa, xb], [ya, yb], linewidth=0.85, color=MAGENTA, alpha=0.8)
    xs_p = [Cp[v][0] for v in Cp]; ys_p = [Cp[v][1] for v in Cp]
    xs_m = [Cm[v][0] for v in Cm]; ys_m = [Cm[v][1] for v in Cm]
    ax.scatter(xs_p, ys_p, s=16, color=CYAN, alpha=0.95)
    ax.scatter(xs_m, ys_m, s=16, color=MAGENTA, alpha=0.95)

    # branchable rings
    xb_p = [Cp[v][0] for v in Cp if v % 6 == ((-2) % 6)]
    yb_p = [Cp[v][1] for v in Cp if v % 6 == ((-2) % 6)]
    xb_m = [Cm[v][0] for v in Cm if v % 6 == (2 % 6)]
    yb_m = [Cm[v][1] for v in Cm if v % 6 == (2 % 6)]
    ax.scatter(xb_p, yb_p, s=42, facecolors='none', edgecolors='k', linewidths=1.1)
    ax.scatter(xb_m, yb_m, s=42, facecolors='none', edgecolors=GRAY, linewidths=1.1)

    # axes / crop
    ax.set_ylim(-0.5, depth + 1.5)
    ax.set_xlim(-xwin, xwin)
    ax.set_ylabel("inverse depth (ground=0, root=1)")
    ax.set_xlabel("number line")

    # dual rulers: bottom B(-1)≡+2 (magenta), top B(+1)≡−2 (cyan)
    series_p = [n for n in range(-xwin, xwin + 1) if n % 6 == ((-2) % 6)]
    series_m = [n for n in range(-xwin, xwin + 1) if n % 6 == (2 % 6)]
    ax.set_xticks(series_m)
    ax.set_xticklabels([str(n) for n in series_m], color=MAGENTA)
    ax.tick_params(axis='x', bottom=True, top=False, labelbottom=True, labeltop=False, labelcolor=MAGENTA)
    secax = ax.secondary_xaxis('top')
    secax.set_xticks(series_p)
    secax.set_xticklabels([str(n) for n in series_p], color=CYAN)
    secax.tick_params(axis='x', labelcolor=CYAN)

    ax.set_title(f"Branching window (depth ≤ {depth}, x∈[-{xwin},{xwin}])")
    plt.tight_layout(); plt.savefig(out, format="pdf"); plt.close(fig)

# -------------------- Coverage (unpruned) ---------------------
def bfs_unpruned_seen(depth: int):
    """Return set of all integers reached within inverse depth ≤ depth for B(+1)."""
    root = 1
    seen = set([root])
    q = deque([(root, 0)])
    while q:
        y, d = q.popleft()
        if d >= depth:
            continue
        for n in preimages_B(y, +1, odd_zero=True):
            if n in seen:
                continue
            seen.add(n)
            q.append((n, d + 1))
    return seen

def coverage_ratio(seen, A: int):
    total = 2 * A + 1
    covered = sum(1 for n in range(-A, A + 1) if n in seen)
    return covered / total, covered, total

def plot_coverage_curves(depths=(2,4,8,16,32), A_list=(10**3,10**4,10**5), out_pdf="bplus1_coverage_curves.pdf", out_csv="bplus1_coverage_unpruned_multiA.csv"):
    rows = []
    ratios_by_A = {A: [] for A in A_list}
    for d in depths:
        seen = bfs_unpruned_seen(d)
        for A in A_list:
            ratio, covered, total = coverage_ratio(seen, A)
            rows.append({"inverse_depth": d, "A": A, "coverage_ratio": ratio, "covered": covered, "total": total, "visited_total": len(seen)})
            ratios_by_A[A].append((d, ratio))
    # CSV
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["inverse_depth","A","coverage_ratio","covered","total","visited_total"])
        w.writeheader(); w.writerows(rows)
    # Plot
    plt.figure(figsize=(7,5))
    for A in A_list:
        xs = [d for d,_ in ratios_by_A[A]]
        ys = [r for _,r in ratios_by_A[A]]
        plt.plot(xs, ys, marker="o", label=f"A={A}")
    plt.xlabel("inverse depth (d)")
    plt.ylabel("coverage ratio in [-A, A]")
    plt.title("B(+1) coverage vs inverse depth (no |n|-pruning)")
    plt.legend()
    plt.tight_layout(); plt.savefig(out_pdf, format="pdf"); plt.close()

# --------------------------- Main -----------------------------
if __name__ == "__main__":
    # 1) B(+1) single (signed log2)
    plot_signedlog_single_Bplus1(depth=10, xlim=12.0, out="signedlog_Bplus1_with_edges.pdf")

    # 2) B(±1) combined (signed log2)
    plot_signedlog_combined_Bpm1(depth=10, xlim=12.0, out="signedlog_Bplus1_Bminus1_with_edges.pdf")

    # 3) W(±1) combined (signed log2) — “鏡の壁”の可視化
    plot_signedlog_combined_Wpm1(depth=10, xlim=12.0, out="signedlog_Wplus1_Wminus1_with_edges.pdf")

    # 4) Branching window (combined, number line, depth≤8, window±60, dual ticks)
    plot_branch_window_combined_dualticks(depth=8, xwin=60, out="branch_window_combined_dualticks_d8.pdf")

    # 5) Coverage curves (unpruned BFS), depths=2,4,8,16,32; A in {1e3,1e4,1e5}
    plot_coverage_curves(depths=(2,4,8,16,32),
                         A_list=(10**3,10**4,10**5),
                         out_pdf="bplus1_coverage_curves.pdf",
                         out_csv="bplus1_coverage_unpruned_multiA.csv")

    print("Done. PDFs and CSV written to current directory.")
