"""
╔══════════════════════════════════════════════════════════════════╗
║           VORONOI DIAGRAM  —  COMPLETE DEMO SUITE               ║
║  Covers: geometry, duality, complexity, GVD, heatmap,           ║
║          animation, Lloyd relaxation, empty-circle theorem       ║
╚══════════════════════════════════════════════════════════════════╝

Requirements:
    pip install numpy scipy matplotlib

Run:
    python voronoi_suite.py
and choose a demo from the menu.
"""

import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay
from matplotlib.colors import LinearSegmentedColormap

# ─── shared style ────────────────────────────────────────────────
DARK_BG   = "#0d1117"
ACCENT    = "#58a6ff"
GOLD      = "#f0c060"
GREEN     = "#3fb950"
RED       = "#f85149"
SOFT_WHITE= "#e6edf3"

def _apply_dark(ax, fig):
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    ax.tick_params(colors=SOFT_WHITE)
    ax.xaxis.label.set_color(SOFT_WHITE)
    ax.yaxis.label.set_color(SOFT_WHITE)
    ax.title.set_color(SOFT_WHITE)

def _random_pts(n=30, lo=0.05, hi=0.95):
    return np.random.rand(n, 2) * (hi - lo) + lo


# ══════════════════════════════════════════════════════════════════
# 1.  STATIC VORONOI  +  DELAUNAY DUAL TOGGLE
# ══════════════════════════════════════════════════════════════════
def demo_static_and_dual():
    """
    Shows the Voronoi diagram and lets you toggle the Delaunay
    triangulation overlay with the 'd' key — the 'dual graph'.
    """
    pts = _random_pts(25)
    vor = Voronoi(pts)
    tri = Delaunay(pts)

    fig, ax = plt.subplots(figsize=(8, 8))
    _apply_dark(ax, fig)
    fig.suptitle("Static Voronoi  ·  press D to toggle Delaunay dual",
                 color=SOFT_WHITE, fontsize=12)

    # ── draw finite Voronoi edges ──
    for simplex in vor.ridge_vertices:
        if -1 not in simplex:
            p0, p1 = vor.vertices[simplex[0]], vor.vertices[simplex[1]]
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=ACCENT, lw=0.8, alpha=0.7)

    # ── Voronoi vertices ──
    vv = vor.vertices
    valid = (vv[:,0]>0)&(vv[:,0]<1)&(vv[:,1]>0)&(vv[:,1]<1)
    ax.scatter(vv[valid,0], vv[valid,1],
               s=18, color=ACCENT, zorder=5, label="Voronoi vertices")

    # ── seed points ──
    ax.scatter(pts[:,0], pts[:,1],
               s=60, color=GOLD, zorder=6, label="Seeds")

    # ── Delaunay (hidden initially) ──
    del_lines = []
    for simp in tri.simplices:
        coords = pts[simp]
        for i in range(3):
            j = (i+1) % 3
            ln, = ax.plot([coords[i,0], coords[j,0]],
                          [coords[i,1], coords[j,1]],
                          color=GREEN, lw=0.9, alpha=0.55, visible=False)
            del_lines.append(ln)

    state = {"dual": False}

    def on_key(event):
        if event.key == "d":
            state["dual"] = not state["dual"]
            for ln in del_lines:
                ln.set_visible(state["dual"])
            label = "Delaunay ON" if state["dual"] else "Delaunay OFF"
            ax.set_title(label, color=GREEN if state["dual"] else SOFT_WHITE,
                         fontsize=10)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("key_press_event", on_key)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    legend = ax.legend(facecolor="#161b22", edgecolor="#30363d",
                       labelcolor=SOFT_WHITE, fontsize=9)
    plt.tight_layout()
    print("  [Static + Dual]  Press 'D' to toggle Delaunay triangulation.")
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 2.  EMPTY-CIRCLE THEOREM  (click a Voronoi vertex → circumcircle)
# ══════════════════════════════════════════════════════════════════
def demo_empty_circle():
    """
    Click any Voronoi vertex and the three seed points that define
    its circumscribed circle are highlighted, with the circle drawn.
    The circle is guaranteed to be empty of all other seeds.
    """
    pts = _random_pts(20)
    vor = Voronoi(pts)
    tri = Delaunay(pts)

    fig, ax = plt.subplots(figsize=(8, 8))
    _apply_dark(ax, fig)
    fig.suptitle("Empty-Circle Theorem  ·  click a Voronoi vertex",
                 color=SOFT_WHITE, fontsize=12)

    # draw Voronoi
    for simplex in vor.ridge_vertices:
        if -1 not in simplex:
            p0, p1 = vor.vertices[simplex[0]], vor.vertices[simplex[1]]
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=ACCENT,
                    lw=0.8, alpha=0.6)

    ax.scatter(pts[:,0], pts[:,1], s=60, color=GOLD, zorder=6)

    # valid vertices inside the unit square
    vv = vor.vertices
    valid_mask = (vv[:,0]>0)&(vv[:,0]<1)&(vv[:,1]>0)&(vv[:,1]<1)
    valid_verts = vv[valid_mask]
    ax.scatter(valid_verts[:,0], valid_verts[:,1],
               s=25, color=ACCENT, zorder=5, picker=True, pickradius=8)

    # persistent artists for the "active" annotation
    circle_patch  = [None]
    tri_artists   = []
    dot_artists   = []

    def _circumcircle(A, B, C):
        """Return (cx, cy, r) of circumcircle of triangle ABC."""
        ax2 = B[0] - A[0]; ay = B[1] - A[1]
        bx2 = C[0] - A[0]; by = C[1] - A[1]
        D = 2 * (ax2*by - ay*bx2)
        if abs(D) < 1e-10:
            return None
        ux = (by*(ax2**2+ay**2) - ay*(bx2**2+by**2)) / D
        uy = (ax2*(bx2**2+by**2) - bx2*(ax2**2+ay**2)) / D
        cx, cy = A[0]+ux, A[1]+uy
        r = np.hypot(cx-A[0], cy-A[1])
        return cx, cy, r

    def on_pick(event):
        nonlocal tri_artists, dot_artists
        # clear previous
        if circle_patch[0]:
            circle_patch[0].remove(); circle_patch[0] = None
        for a in tri_artists + dot_artists:
            a.remove()
        tri_artists.clear(); dot_artists.clear()

        click_pt = np.array([event.mouseevent.xdata,
                             event.mouseevent.ydata])
        if click_pt[0] is None:
            return

        # find nearest valid vertex
        dists = np.linalg.norm(valid_verts - click_pt, axis=1)
        idx   = np.argmin(dists)
        vx, vy = valid_verts[idx]

        # find the 3 nearest seed points (= the circumcircle seeds)
        seed_dists = np.linalg.norm(pts - [vx, vy], axis=1)
        nearest3   = np.argsort(seed_dists)[:3]
        A, B, C    = pts[nearest3]

        circ = _circumcircle(A, B, C)
        if circ is None:
            return
        cx, cy, r = circ

        # draw circumcircle
        c = plt.Circle((cx, cy), r, fill=False,
                        edgecolor=RED, lw=1.5, linestyle="--", zorder=7)
        ax.add_patch(c)
        circle_patch[0] = c

        # draw triangle edges
        for i in range(3):
            j = (i+1)%3
            ln, = ax.plot([pts[nearest3[i],0], pts[nearest3[j],0]],
                          [pts[nearest3[i],1], pts[nearest3[j],1]],
                          color=GREEN, lw=1.2, zorder=8)
            tri_artists.append(ln)

        # highlight the 3 seeds
        for p in [A, B, C]:
            d, = ax.plot(p[0], p[1], "o", color=RED,
                         ms=9, zorder=9)
            dot_artists.append(d)

        # show vertex
        vd, = ax.plot(vx, vy, "*", color=SOFT_WHITE, ms=12, zorder=10)
        dot_artists.append(vd)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    plt.tight_layout()
    print("  [Empty Circle]  Click a blue vertex to reveal its circumcircle.")
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 3.  O(n log n) PERFORMANCE BENCHMARKER
# ══════════════════════════════════════════════════════════════════
def demo_complexity():
    """
    Times scipy Voronoi for n = 10 … 50 000 points, then plots
    execution time alongside a fitted n·log₂(n) reference curve.
    """
    sizes  = np.logspace(1, 4.7, 30).astype(int)
    times  = []

    print("  Benchmarking … ", end="", flush=True)
    for n in sizes:
        pts = np.random.rand(n, 2)
        t0  = time.perf_counter()
        Voronoi(pts)
        times.append(time.perf_counter() - t0)
        print(".", end="", flush=True)
    print(" done.")

    times = np.array(times)

    # fit  t ≈ k · n · log2(n)
    nlogn = sizes * np.log2(sizes)
    k     = np.dot(nlogn, times) / np.dot(nlogn, nlogn)
    fit   = k * nlogn

    fig, ax = plt.subplots(figsize=(9, 5))
    _apply_dark(ax, fig)
    fig.suptitle("Algorithmic Complexity  ·  scipy Voronoi",
                 color=SOFT_WHITE, fontsize=12)

    ax.loglog(sizes, times * 1000, "o", color=GOLD,
              ms=5, label="Measured time (ms)", zorder=5)
    ax.loglog(sizes, fit  * 1000, "--", color=RED,
              lw=1.8, label=f"O(n log n) fit  (k={k*1e6:.2f} µs)")

    ax.set_xlabel("Number of seed points  n")
    ax.set_ylabel("Time (ms)")
    ax.legend(facecolor="#161b22", edgecolor="#30363d",
              labelcolor=SOFT_WHITE, fontsize=10)
    ax.grid(True, which="both", color="#30363d", lw=0.5)
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 4a.  GVD PROXY  —  "wall" built from densely packed seeds
# ══════════════════════════════════════════════════════════════════
def demo_gvd_proxy():
    """
    Two L-shaped walls are simulated by placing seeds very close
    together along line segments.  The Voronoi edges naturally form
    the 'middle-of-the-hallway' path between the walls.
    A red start→goal arrow hints at path planning.
    """
    def wall(p0, p1, n=60):
        t = np.linspace(0, 1, n)
        return np.column_stack([p0[0] + t*(p1[0]-p0[0]),
                                 p0[1] + t*(p1[1]-p0[1])])

    # two L-shaped walls
    wall_pts = np.vstack([
        wall([0.10, 0.20], [0.90, 0.20]),   # bottom wall
        wall([0.10, 0.80], [0.90, 0.80]),   # top wall
        wall([0.10, 0.20], [0.10, 0.80]),   # left wall
        wall([0.50, 0.20], [0.50, 0.50]),   # inner divider
    ])

    # add a handful of random "obstacle posts" in the corridor
    extra = _random_pts(6, lo=0.2, hi=0.8)
    all_pts = np.vstack([wall_pts, extra])

    vor = Voronoi(all_pts)

    fig, ax = plt.subplots(figsize=(8, 8))
    _apply_dark(ax, fig)
    fig.suptitle("Generalized Voronoi Diagram Proxy  ·  walls as dense seeds",
                 color=SOFT_WHITE, fontsize=12)

    # draw Voronoi edges clipped to [0,1]²
    for ridge in vor.ridge_vertices:
        if -1 in ridge:
            continue
        p0, p1 = vor.vertices[ridge[0]], vor.vertices[ridge[1]]
        if (0<=p0[0]<=1 and 0<=p0[1]<=1 and
            0<=p1[0]<=1 and 0<=p1[1]<=1):
            ax.plot([p0[0],p1[0]], [p0[1],p1[1]],
                    color=ACCENT, lw=0.7, alpha=0.55)

    # draw wall seeds (tiny)
    ax.scatter(wall_pts[:,0], wall_pts[:,1],
               s=3, color="#888888", zorder=4, label="Wall seeds")
    ax.scatter(extra[:,0], extra[:,1],
               s=40, color=RED, zorder=5, marker="^", label="Obstacle posts")

    # illustrative start / goal
    ax.annotate("", xy=(0.70, 0.50), xytext=(0.20, 0.50),
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))
    ax.text(0.20, 0.52, "Start", color=GREEN, fontsize=9)
    ax.text(0.67, 0.52, "Goal",  color=GREEN, fontsize=9)

    ax.set_xlim(0,1); ax.set_ylim(0,1)
    legend = ax.legend(facecolor="#161b22", edgecolor="#30363d",
                       labelcolor=SOFT_WHITE, fontsize=9)
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 4b.  CLEARANCE HEATMAP  (distance-to-nearest-seed background)
# ══════════════════════════════════════════════════════════════════
def demo_clearance_heatmap():
    """
    Rasterises a 400×400 grid; each pixel is coloured by its
    distance to the nearest seed point.
    Voronoi edges are the *ridges* (local maxima) of this surface —
    i.e. the safest paths for a robot to travel.
    """
    n_seeds = 20
    pts = _random_pts(n_seeds)
    vor = Voronoi(pts)

    res = 400
    xs = np.linspace(0, 1, res)
    ys = np.linspace(0, 1, res)
    gx, gy = np.meshgrid(xs, ys)
    grid   = np.stack([gx, gy], axis=-1)          # (res, res, 2)

    # distance of every pixel to its nearest seed
    diffs = grid[:,:,np.newaxis,:] - pts[np.newaxis,np.newaxis,:,:]
    dist  = np.min(np.linalg.norm(diffs, axis=-1), axis=-1)

    # custom colormap: dark purple → bright cyan
    cmap = LinearSegmentedColormap.from_list(
        "clearance", ["#0d1117", "#1a3a5c", "#1e90ff", "#00ffe0"])

    fig, ax = plt.subplots(figsize=(8, 8))
    _apply_dark(ax, fig)
    fig.suptitle("Clearance Heatmap  ·  Voronoi edges = safety ridges",
                 color=SOFT_WHITE, fontsize=12)

    im = ax.imshow(dist, origin="lower", extent=[0,1,0,1],
                   cmap=cmap, vmin=0, vmax=dist.max(), zorder=1)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cb.set_label("Distance to nearest obstacle", color=SOFT_WHITE)
    cb.ax.yaxis.set_tick_params(color=SOFT_WHITE)
    plt.setp(cb.ax.yaxis.get_ticklabels(), color=SOFT_WHITE)

    # overlay Voronoi edges
    for ridge in vor.ridge_vertices:
        if -1 in ridge:
            continue
        p0, p1 = vor.vertices[ridge[0]], vor.vertices[ridge[1]]
        ax.plot([p0[0],p1[0]], [p0[1],p1[1]],
                color="white", lw=0.9, alpha=0.8, zorder=3)

    ax.scatter(pts[:,0], pts[:,1],
               s=50, color=GOLD, zorder=5, label="Seeds")

    ax.set_xlim(0,1); ax.set_ylim(0,1)
    legend = ax.legend(facecolor="#161b22", edgecolor="#30363d",
                       labelcolor=SOFT_WHITE, fontsize=9)
    plt.tight_layout()
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 5.  POINT-ADDITION ANIMATION  (click to add seeds)
# ══════════════════════════════════════════════════════════════════
def demo_point_addition():
    """
    Left-click anywhere in the canvas to add a seed and watch the
    Voronoi diagram reconfigure instantly — illustrating the
    'fragility' of the partition.
    """
    pts = list(_random_pts(5))          # start with 5 seeds

    fig, ax = plt.subplots(figsize=(7, 7))
    _apply_dark(ax, fig)
    fig.suptitle("Point-Addition  ·  click to add seeds",
                 color=SOFT_WHITE, fontsize=11)
    ax.set_xlim(0,1); ax.set_ylim(0,1)

    edge_collection = [None]
    seed_scatter    = [None]
    vert_scatter    = [None]
    count_text      = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                              color=SOFT_WHITE, fontsize=9, va="top")

    def redraw():
        arr = np.array(pts)
        if arr.shape[0] < 4:
            return

        # clear previous
        for artist_list in [edge_collection, seed_scatter, vert_scatter]:
            if artist_list[0]:
                artist_list[0].remove()
                artist_list[0] = None

        vor = Voronoi(arr)

        # edges
        segments = []
        for ridge in vor.ridge_vertices:
            if -1 not in ridge:
                p0, p1 = vor.vertices[ridge[0]], vor.vertices[ridge[1]]
                segments.append([p0, p1])
        lc = LineCollection(segments, colors=ACCENT,
                            linewidths=0.9, alpha=0.75)
        ax.add_collection(lc)
        edge_collection[0] = lc

        # vertices
        vv = vor.vertices
        vm = (vv[:,0]>0)&(vv[:,0]<1)&(vv[:,1]>0)&(vv[:,1]<1)
        vert_scatter[0] = ax.scatter(vv[vm,0], vv[vm,1],
                                     s=15, color=ACCENT, zorder=5)

        # seeds
        seed_scatter[0] = ax.scatter(arr[:,0], arr[:,1],
                                     s=55, color=GOLD, zorder=6)

        count_text.set_text(f"Seeds: {len(pts)}")
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax or event.button != 1:
            return
        pts.append([event.xdata, event.ydata])
        redraw()

    fig.canvas.mpl_connect("button_press_event", on_click)
    redraw()
    plt.tight_layout()
    print("  [Point Addition]  Left-click the canvas to add seed points.")
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 6.  LLOYD'S ALGORITHM  (Centroidal Voronoi relaxation)
# ══════════════════════════════════════════════════════════════════
def _voronoi_cell_centroid(vor, region_idx, pts, bounds=(0,1,0,1)):
    """
    Approximate the centroid of a Voronoi cell by sampling the polygon.
    Falls back to the seed if the region is open/degenerate.
    """
    from matplotlib.patches import Polygon as MplPoly
    from matplotlib.path   import Path

    region = vor.regions[region_idx]
    if -1 in region or len(region) == 0:
        return None

    verts = vor.vertices[region]

    # clip to bounding box (simple rejection sampling)
    x0, x1, y0, y1 = bounds
    path = Path(verts)
    xs = np.random.uniform(x0, x1, 2000)
    ys = np.random.uniform(y0, y1, 2000)
    inside = path.contains_points(np.column_stack([xs, ys]))
    if inside.sum() < 3:
        return None
    return np.array([xs[inside].mean(), ys[inside].mean()])


def demo_lloyds():
    """
    Lloyd's Algorithm: iteratively replace each seed with the
    centroid of its Voronoi cell.  Press Enter to step, or let the
    animation run automatically.
    """
    n_pts   = 40
    pts     = _random_pts(n_pts)
    max_itr = 30

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    ax_vor, ax_energy = axes
    _apply_dark(ax_vor, fig)
    _apply_dark(ax_energy, fig)
    fig.suptitle("Lloyd's Algorithm  ·  Centroidal Voronoi Relaxation",
                 color=SOFT_WHITE, fontsize=12)

    energies  = []
    itr_count = [0]

    # ── right panel: energy curve ──
    ax_energy.set_xlabel("Iteration")
    ax_energy.set_ylabel("Centroidal energy (avg sq. displacement)")
    ax_energy.set_title("Convergence", color=SOFT_WHITE)
    ax_energy.grid(True, color="#30363d", lw=0.5)
    energy_line, = ax_energy.plot([], [], color=RED, lw=1.5)

    # ── left panel persistent artists ──
    edge_col  = [None]
    seed_scat = [None]
    iter_text = ax_vor.text(0.02, 0.97, "", transform=ax_vor.transAxes,
                            color=SOFT_WHITE, fontsize=9, va="top")

    def draw_voronoi(cur_pts):
        if edge_col[0]:
            edge_col[0].remove()
        if seed_scat[0]:
            seed_scat[0].remove()

        vor = Voronoi(cur_pts)
        segs = []
        for r in vor.ridge_vertices:
            if -1 not in r:
                p0, p1 = vor.vertices[r[0]], vor.vertices[r[1]]
                segs.append([p0, p1])
        lc = LineCollection(segs, colors=ACCENT, linewidths=0.8, alpha=0.7)
        ax_vor.add_collection(lc)
        edge_col[0]  = lc
        seed_scat[0] = ax_vor.scatter(cur_pts[:,0], cur_pts[:,1],
                                      s=30, color=GOLD, zorder=5)
        ax_vor.set_xlim(0,1); ax_vor.set_ylim(0,1)

    def lloyd_step(cur_pts):
        vor = Voronoi(cur_pts)
        new_pts = cur_pts.copy()
        for i, pt_region in enumerate(vor.point_region):
            c = _voronoi_cell_centroid(vor, pt_region, cur_pts)
            if c is not None:
                new_pts[i] = c
        energy = np.mean(np.linalg.norm(new_pts - cur_pts, axis=1)**2)
        return new_pts, energy

    def animate(_frame):
        nonlocal pts
        if itr_count[0] >= max_itr:
            return
        pts, e = lloyd_step(pts)
        energies.append(e)
        itr_count[0] += 1
        draw_voronoi(pts)
        iter_text.set_text(f"Iteration {itr_count[0]}/{max_itr}")
        energy_line.set_data(range(len(energies)), energies)
        ax_energy.relim(); ax_energy.autoscale_view()
        fig.canvas.draw_idle()

    draw_voronoi(pts)
    anim = animation.FuncAnimation(fig, animate, frames=max_itr,
                                   interval=180, repeat=False)
    plt.tight_layout()
    print("  [Lloyd's Algorithm]  Watch seeds migrate to cell centroids.")
    plt.show()
    return anim   # keep reference alive


# ══════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════
DEMOS = {
    "1": ("Static Voronoi + Delaunay Dual  [press D]",    demo_static_and_dual),
    "2": ("Empty-Circle Theorem  [click a vertex]",        demo_empty_circle),
    "3": ("O(n log n) Complexity Benchmark",               demo_complexity),
    "4": ("GVD Proxy  (walls as dense seeds)",             demo_gvd_proxy),
    "5": ("Clearance Heatmap",                             demo_clearance_heatmap),
    "6": ("Point-Addition  [click to add seeds]",          demo_point_addition),
    "7": ("Lloyd's Algorithm  (centroidal relaxation)",    demo_lloyds),
    "a": ("Run ALL demos in sequence",                     None),
}

def main():
    matplotlib.rcParams.update({
        "figure.facecolor": DARK_BG,
        "axes.facecolor":   DARK_BG,
        "text.color":       SOFT_WHITE,
    })
    np.random.seed(42)

    print("\n" + "═"*56)
    print("   VORONOI DIAGRAM  ·  DEMO SUITE")
    print("═"*56)
    for key, (label, _) in DEMOS.items():
        print(f"  [{key}]  {label}")
    print("  [q]  Quit")
    print("═"*56)

    while True:
        choice = input("\nSelect demo: ").strip().lower()
        if choice == "q":
            print("Bye!")
            break
        elif choice == "a":
            for key, (label, fn) in DEMOS.items():
                if fn is not None:
                    print(f"\n── {label} ──")
                    fn()
        elif choice in DEMOS and DEMOS[choice][1]:
            label, fn = DEMOS[choice]
            print(f"\n── {label} ──")
            fn()
        else:
            print("  Unknown option, try again.")


if __name__ == "__main__":
    main()