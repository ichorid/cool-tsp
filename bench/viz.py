"""Matplotlib visualization for TSP routes (dev/demo)."""

import matplotlib.pyplot as plt

from mytsp.models import CoolTspSolution, NodeType, TSPInstance, TSPSolution


def plot_cool_route(
    result: CoolTspSolution,
    *,
    title: str | None = None,
    show_labels: bool = True,
) -> None:
    """Plot CoolTsp: green start, blue delivery, magenta detour/pickup, red unused."""
    nodes = result.nodes
    unused = result.unused_nodes

    plt.figure(figsize=(8, 6))
    if nodes:
        # result.nodes is already in visit order; draw tour by sequential index.
        coords = [(n.x, n.y) for n in nodes]
        n_pts = len(nodes)
        pickup_idx = next(
            (i for i, n in enumerate(nodes) if n.node_type == NodeType.PICKUP), None
        )

        # Draw main tour in blue (all edges first).
        closed = list(range(n_pts)) + [0]
        xs = [coords[i][0] for i in closed]
        ys = [coords[i][1] for i in closed]
        plt.plot(xs, ys, "b-", linewidth=2, label="tour", zorder=1)

        # Draw detour edges (into and out of pickup) in magenta.
        if pickup_idx is not None:
            prev_i = (pickup_idx - 1) % n_pts
            next_i = (pickup_idx + 1) % n_pts
            for i, j in [(prev_i, pickup_idx), (pickup_idx, next_i)]:
                plt.plot(
                    [coords[i][0], coords[j][0]],
                    [coords[i][1], coords[j][1]],
                    "m-",
                    linewidth=2.5,
                    zorder=2,
                )
            plt.plot([], [], "m-", linewidth=2.5, label="detour")

        # Points: start green, delivery blue, pickup (in route) magenta.
        start_pts = [(n.x, n.y) for n in nodes if n.node_type == NodeType.START]
        delivery_pts = [(n.x, n.y) for n in nodes if n.node_type == NodeType.DELIVERY]
        pickup_pts = [(n.x, n.y) for n in nodes if n.node_type == NodeType.PICKUP]
        if start_pts:
            sx, sy = zip(*start_pts, strict=True)
            plt.scatter(
                sx, sy, c="green", s=120, zorder=5, label="start", edgecolors="darkgreen"
            )
        if delivery_pts:
            dx, dy = zip(*delivery_pts, strict=True)
            plt.scatter(dx, dy, c="blue", s=80, zorder=5, label="delivery")
        if pickup_pts:
            px, py = zip(*pickup_pts, strict=True)
            plt.scatter(
                px,
                py,
                c="magenta",
                s=80,
                zorder=5,
                label="pickup",
                edgecolors="darkmagenta",
            )
        if show_labels:
            for i, (x, y) in enumerate(coords):
                plt.annotate(str(i), (x, y), fontsize=10, ha="center", va="bottom")
    if unused:
        ux = [n.x for n in unused]
        uy = [n.y for n in unused]
        plt.scatter(ux, uy, c="red", s=80, zorder=5, label="pickup (unused)")
    plt.title(title or f"Tour length: {result.solution.distance:.2f}")
    plt.axis("equal")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_route(
    instance: TSPInstance,
    solution: TSPSolution,
    *,
    title: str | None = None,
    show_labels: bool = True,
) -> None:
    """Plot a TSP route as a closed tour with numbered nodes."""
    coords = [(n.x, n.y) for n in instance.nodes]
    route = solution.route + [solution.route[0]]  # close the loop
    xs = [coords[i][0] for i in route]
    ys = [coords[i][1] for i in route]

    plt.figure(figsize=(8, 6))
    plt.plot(xs, ys, "b-o", linewidth=2, markersize=8)
    if show_labels:
        for i, (x, y) in enumerate(coords):
            plt.annotate(str(i), (x, y), fontsize=10, ha="center", va="bottom")
    plt.title(title or f"Tour length: {solution.distance:.2f}")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()
