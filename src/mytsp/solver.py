"""Solver interface and reference implementations."""

import math
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from itertools import combinations, pairwise
from typing import Any, Protocol, TypedDict, TypeVar, cast

from mytsp.models import TSPInstance, TSPSolution

T = TypeVar("T")


class _HasXY(Protocol):
    x: float
    y: float


def _dist(a: _HasXY, b: _HasXY) -> float:
    """Euclidean distance between two point-like objects (Node or NodeData)."""
    return math.hypot(a.x - b.x, a.y - b.y)


def _cyclic_pairs[T](seq: Sequence[T]) -> Iterator[tuple[T, T]]:
    """Yield consecutive pairs wrapping the last element back to the first."""
    yield from pairwise(seq)
    if len(seq) > 1:
        yield (seq[-1], seq[0])


class SolverStats(TypedDict):
    """Optional solver statistics (e.g. 2-opt iterations)."""

    initial_distance: float
    final_distance: float
    iteration_count: int
    improving_iteration_count: int
    distance_history: list[float]


class Solver(ABC):
    """Abstract base class for TSP solvers."""

    def solve(self, instance: TSPInstance) -> TSPSolution:
        """Solve the given TSP instance and return a solution."""
        return self._solve(instance)

    @abstractmethod
    def _solve(self, instance: TSPInstance) -> TSPSolution:
        """Solve the given TSP instance and return a solution."""
        ...


class NaiveSolver(Solver):
    """Reference solver: brute-force for tiny instances (template only)."""

    def _solve(self, instance: TSPInstance) -> TSPSolution:
        # Placeholder: visit nodes in given order and compute distance
        route = list(range(len(instance.nodes)))
        route_nodes = [instance.nodes[i] for i in route]
        distance = sum(_dist(a, b) for a, b in _cyclic_pairs(route_nodes))
        return TSPSolution(route=route, distance=distance)


@dataclass
class Neighbor:
    index: int
    distance: float


@dataclass
class NodeData:
    index: int
    x: float
    y: float
    neighbors: list[Neighbor]


@dataclass
class Edge:
    start: NodeData
    end: NodeData
    length: float


def _build_node_data(instance: TSPInstance) -> list[NodeData]:
    """Build sorted neighbor lists for each node."""
    nodes = instance.nodes
    n = len(nodes)
    neighbor_lists: list[list[Neighbor]] = [[] for _ in range(n)]

    for i, j in combinations(range(n), 2):
        dist = _dist(nodes[i], nodes[j])
        neighbor_lists[i].append(Neighbor(index=j, distance=dist))
        neighbor_lists[j].append(Neighbor(index=i, distance=dist))

    return [
        NodeData(
            index=i,
            x=nodes[i].x,
            y=nodes[i].y,
            neighbors=sorted(nb, key=lambda x: x.distance),
        )
        for i, nb in enumerate(neighbor_lists)
    ]


class NearestNeighborSolver(Solver):
    """Nearest-neighbor solver."""

    def solve_and_get_node_data(
        self, instance: TSPInstance
    ) -> tuple[TSPSolution, list[NodeData]]:
        # Solve and return both solution and cached distances between the nodes,
        # to e.g. use with further refinement algorithms
        node_data = _build_node_data(instance)
        route_list: list[int] = [node_data[0].index]
        route_set: set[int] = {node_data[0].index}
        route_length = 0.0

        while len(route_list) < len(node_data):
            current = node_data[route_list[-1]]
            for nb in current.neighbors:
                if nb.index not in route_set:
                    route_list.append(nb.index)
                    route_set.add(nb.index)
                    route_length += nb.distance
                    break
            else:
                break  # no unvisited neighbor

        route_length += _dist(node_data[route_list[-1]], node_data[route_list[0]])

        return TSPSolution(route=route_list, distance=route_length), node_data

    def _solve(self, instance: TSPInstance) -> TSPSolution:
        return self.solve_and_get_node_data(instance)[0]


class Simple2PointSolver(Solver):
    def __init__(self, max_iterations: int = 100) -> None:
        self.max_iterations = max_iterations

    def _solve(self, instance: TSPInstance) -> TSPSolution:
        stats: SolverStats = {
            "initial_distance": 0.0,
            "final_distance": 0.0,
            "iteration_count": 0,
            "improving_iteration_count": 0,
            "distance_history": [],
        }

        nn_solution, nodes = NearestNeighborSolver().solve_and_get_node_data(instance)
        route = nn_solution.route.copy()

        route_nodes = [nodes[route[i]] for i in range(len(route))]
        edges = [Edge(a, b, _dist(a, b)) for a, b in _cyclic_pairs(route_nodes)]
        stats["initial_distance"] = sum(e.length for e in edges)

        used_start_edges: set[tuple[int, int]] = set()

        for _ in range(self.max_iterations):
            edges = self._rotate_to_longest_unused(edges, used_start_edges)
            optimized = self.optimize_edges(edges)
            stats["iteration_count"] += 1
            stats["distance_history"].append(sum(e.length for e in edges))
            if optimized is None:
                break
            stats["improving_iteration_count"] += 1
            edges = optimized

        stats["final_distance"] = sum(e.length for e in edges)
        return self.edges_to_solution(edges, stats)

    def _rotate_to_longest_unused(
        self, edges: list[Edge], used_start_edges: set[tuple[int, int]]
    ) -> list[Edge]:
        """Rotate so longest unused-as-start edge is first. Mutates used_start_edges."""
        if not edges:
            return edges

        def edge_canonical(e: Edge) -> tuple[int, int]:
            return (min(e.start.index, e.end.index), max(e.start.index, e.end.index))

        all_canonical = {edge_canonical(e) for e in edges}
        available = all_canonical - used_start_edges
        if not available:
            return edges
        cand = (i for i in range(len(edges)) if edge_canonical(edges[i]) in available)
        k = max(cand, key=lambda i: edges[i].length)
        used_start_edges.add(edge_canonical(edges[k]))
        return edges[k:] + edges[:k]

    def edges_to_solution(
        self, edges: list[Edge], stats: SolverStats | None = None
    ) -> TSPSolution:
        """Convert edges (cycle) into ordered route and total distance."""
        if not edges:
            return TSPSolution(
                route=[], distance=0.0, stats=cast("dict[str, Any] | None", stats)
            )

        adj: dict[int, list[int]] = defaultdict(list)
        total_length = 0.0
        for e in edges:
            total_length += e.length
            s, t = e.start.index, e.end.index
            adj[s].append(t)
            adj[t].append(s)

        start = edges[0].start.index
        route = [start]
        prev, cur = start, adj[start][0]
        while cur != start:
            route.append(cur)
            next_nodes = adj[cur]
            nxt = next_nodes[1] if next_nodes[0] == prev else next_nodes[0]
            prev, cur = cur, nxt

        return TSPSolution(
            route=route, distance=total_length, stats=cast(dict[str, Any] | None, stats)
        )

    def optimize_edges(self, edges: list[Edge]) -> list[Edge] | None:
        """Best 2-opt move over non-adjacent pairs, or None. Edges in tour order."""
        n = len(edges)
        best_saving = 0.0
        best: tuple[int, int] | None = None
        for i, j in combinations(range(n), 2):
            if j - i == 1 or (i == 0 and j == n - 1):
                continue
            saving = self._swap_saving(edges, i, j)
            if saving > best_saving:
                best_saving = saving
                best = (i, j)
        if best is None:
            return None
        return self._apply_swap(edges, best[0], best[1])

    def _swap_saving(self, edges: list[Edge], i: int, j: int) -> float:
        """Return the distance saved by swapping edges i and j, or 0 if no improvement."""
        edge_i, edge_j = edges[i], edges[j]
        a, b = edge_i.start, edge_i.end
        c, d = edge_j.start, edge_j.end
        new_cost = _dist(a, c) + _dist(b, d)
        old_cost = edge_i.length + edge_j.length
        saving = old_cost - new_cost
        return max(0.0, saving)

    def _apply_swap(self, edges: list[Edge], i: int, j: int) -> list[Edge]:
        """2-opt: remove edges i,j; add (a,c) and (b,d); reverse segment between."""
        a, b = edges[i].start, edges[i].end
        c, d = edges[j].start, edges[j].end
        dist_ac = _dist(a, c)
        dist_bd = _dist(b, d)
        new_edges: list[Edge] = []
        new_edges.extend(edges[:i])
        new_edges.append(Edge(a, c, dist_ac))
        for k in range(j - 1, i, -1):
            e = edges[k]
            new_edges.append(Edge(e.end, e.start, e.length))
        new_edges.append(Edge(b, d, dist_bd))
        new_edges.extend(edges[j + 1 :])
        return new_edges
