"""CoolTsp solver: delivery/pickup problem with injected TSP solver.

Pipeline (see algo_explainer.md):
  1. Select deliveries via trivial knapsack (demand ascending).
  2. Solve TSP over depot + selected deliveries.
  3. Pickup insertion (post-processing only — no TSP re-solve):
     a. Build a detour accelerator per pickup (sorted delta list).
     b. Simulate load profile in both travel directions.
     c. Walk each accelerator cheapest-first; first feasible edge wins.
     d. Among all pickups, pick the one with smallest delta.
     e. Splice the winner into the route, reversing direction if needed.
"""

import math
from dataclasses import dataclass

from mytsp.models import (
    CoolTspProblem,
    CoolTspSolution,
    Node,
    NodeType,
    TSPInstance,
    TSPSolution,
)
from mytsp.solver import Solver


@dataclass
class DetourEntry:
    """Detour cost and edge index for a pickup insertion."""

    delta: float  # dist(A,P) + dist(P,B) - dist(A,B)
    edge_index: int  # sequential edge in the route


@dataclass
class PickupCandidate:
    """Best feasible insertion for one pickup."""

    pickup: Node
    pickup_index: int  # index in the pickups list (for index-based filtering)
    delta: float
    edge_index: int
    reverse: bool  # True => must reverse route direction


def _with_type(n: Node, node_type: NodeType) -> Node:
    """Return a copy of the node with node_type set."""
    return n.model_copy(update={"node_type": node_type})


def _dist(a: Node, b: Node) -> float:
    """Euclidean distance between two nodes."""
    return math.dist((a.x, a.y), (b.x, b.y))


def _build_detour_accelerator(pickup: Node, route_nodes: list[Node]) -> list[DetourEntry]:
    """Build the detour accelerator for one pickup.

    For every route edge A->B, the detour delta is:
        delta = dist(A,P) + dist(P,B) - dist(A,B)
    By the triangle inequality delta >= 0; a small delta means P lies
    near edge A->B. Sorting ascending lets us walk front-to-back and
    stop at the first feasible edge (guaranteed cheapest).
    """
    n = len(route_nodes)
    if n < 2:
        return []
    entries: list[DetourEntry] = []
    for i in range(n):
        a = route_nodes[i]
        b = route_nodes[(i + 1) % n]
        base = _dist(a, b)
        detour = _dist(a, pickup) + _dist(pickup, b)
        delta = detour - base
        entries.append(DetourEntry(delta=delta, edge_index=i))
    entries.sort(key=lambda e: e.delta)
    return entries


def _compute_load_profile(route_nodes: list[Node]) -> list[tuple[float, float]]:
    """Simulate vehicle load in both travel directions.

    The vehicle starts at the depot carrying all packages. As it visits
    each delivery, the load decreases. Because the route is a cycle, it
    can be traversed in either direction — we simulate both independently
    so the feasibility check can try direct or reverse for each edge in one step.

    Returns (direct_load, reverse_load) per route position.
    """
    n = len(route_nodes)
    if n == 0:
        return []
    total_demand = sum(node.demand for node in route_nodes)
    direct_load: list[float] = [0.0] * n
    direct_load[0] = total_demand
    for i in range(1, n):
        direct_load[i] = direct_load[i - 1] - route_nodes[i].demand

    reverse_load: list[float] = [0.0] * n
    reverse_load[0] = total_demand
    reverse_load[n - 1] = total_demand - route_nodes[n - 1].demand
    for i in range(n - 2, 0, -1):
        reverse_load[i] = reverse_load[i + 1] - route_nodes[i].demand

    return list(zip(direct_load, reverse_load, strict=True))


def _find_best_insertion(
    pickup: Node,
    pickup_index: int,
    accelerator: list[DetourEntry],
    load_profile: list[tuple[float, float]],
    capacity: float,
) -> PickupCandidate | None:
    """Walk the accelerator cheapest-first; return first feasible edge.

    Because the accelerator is sorted by delta, the first edge where the
    pickup fits is guaranteed to be the cheapest insertion for this pickup.
    Direct traversal is preferred; reverse is tried only if direct fails.
    """
    n = len(load_profile)
    if n == 0:
        return None
    for entry in accelerator:
        i = entry.edge_index
        direct_load = load_profile[i][0]
        rev_load = load_profile[(i + 1) % n][1]
        direct_ok = direct_load + pickup.demand <= capacity
        reverse_ok = rev_load + pickup.demand <= capacity
        if direct_ok:
            return PickupCandidate(
                pickup=pickup,
                pickup_index=pickup_index,
                delta=entry.delta,
                edge_index=i,
                reverse=False,
            )
        if reverse_ok:
            return PickupCandidate(
                pickup=pickup,
                pickup_index=pickup_index,
                delta=entry.delta,
                edge_index=i,
                reverse=True,
            )
    return None


def _select_best_pickup(
    pickups: list[Node],
    route_nodes: list[Node],
    capacity: float,
) -> PickupCandidate | None:
    """Global candidate selection: smallest delta across all pickups (algo §6).

    Each pickup independently yields at most one PickupCandidate (its
    cheapest feasible insertion). We keep the global minimum delta.
    The load profile is computed once and shared — O(P * E) total.
    """
    if not pickups or len(route_nodes) < 2:
        return None
    load_profile = _compute_load_profile(route_nodes)
    best: PickupCandidate | None = None
    for idx, pickup in enumerate(pickups):
        accelerator = _build_detour_accelerator(pickup, route_nodes)
        candidate = _find_best_insertion(pickup, idx, accelerator, load_profile, capacity)
        if candidate is not None and (best is None or candidate.delta < best.delta):
            best = candidate
    return best


def _route_distance(nodes: list[Node]) -> float:
    """Total distance of a closed tour: consecutive edges plus closing edge."""
    if len(nodes) < 2:
        return 0.0
    total = 0.0
    for i in range(len(nodes)):
        total += _dist(nodes[i], nodes[(i + 1) % len(nodes)])
    return total


def _insert_pickup(
    route_nodes: list[Node],
    pickup: Node,
    edge_index: int,
    reverse: bool,
) -> list[Node]:
    """Splice the pickup into the route at the selected edge.

    Breaks edge A->B into A->P->B. If `reverse` is True the delivery
    portion is reversed first (depot stays at index 0) so the vehicle
    approaches the insertion edge from the direction that has capacity.
    """
    nodes = list(route_nodes)
    n = len(nodes)
    if reverse:
        # [depot, d1, d2, ..., dk] -> [depot, dk, ..., d1]
        nodes = [nodes[0]] + list(reversed(nodes[1:]))
        # Original edge i becomes edge (n - 1 - i) in reversed route
        edge_index = n - 1 - edge_index
    pickup_node = _with_type(pickup, NodeType.PICKUP)
    # Insert after nodes[edge_index], before nodes[edge_index + 1]
    insert_at = edge_index + 1
    return nodes[:insert_at] + [pickup_node] + nodes[insert_at:]


def _trivial_knapsack(deliveries: list[Node], capacity: float) -> list[Node]:
    """Trivial knapsack: sort by demand ascending, add until capacity."""
    sorted_deliveries = sorted(deliveries, key=lambda n: n.demand)
    selected: list[Node] = []
    total_demand = 0.0
    for node in sorted_deliveries:
        if total_demand + node.demand <= capacity:
            selected.append(node)
            total_demand += node.demand
        else:
            break
    return selected


class CoolSolver:
    """Solve CoolTsp via injected TSP solver; optionally inserts one pickup per route."""

    def __init__(self, tsp_solver: Solver) -> None:
        """Initialize with the TSP solver to use for the delivery subproblem."""
        self._tsp_solver = tsp_solver

    def solve(self, problem: CoolTspProblem) -> CoolTspSolution:
        """Run the full pipeline (algo §1): knapsack -> TSP -> pickup insertion."""
        # See algo_explainer.md for the full pipeline explanation
        pickups = problem.pickups
        start_node = _with_type(problem.start, NodeType.START)

        # greedy knapsack selects deliveries that fit capacity
        selected = _trivial_knapsack(problem.deliveries, problem.vehicle_capacity)
        delivery_nodes = [_with_type(n, NodeType.DELIVERY) for n in selected]
        tour_nodes = [start_node] + delivery_nodes

        # solve TSP over depot + selected deliveries
        instance = TSPInstance(nodes=tour_nodes)
        solution = self._tsp_solver.solve(instance)
        nodes_in_route_order = [tour_nodes[i] for i in solution.route]

        # pickup insertion — post-processing only, no TSP re-solve
        best = _select_best_pickup(
            pickups, nodes_in_route_order, problem.vehicle_capacity
        )
        if best is not None:
            # splice winner into the route
            nodes_in_route_order = _insert_pickup(
                nodes_in_route_order,
                best.pickup,
                best.edge_index,
                best.reverse,
            )
            distance = _route_distance(nodes_in_route_order)
            solution = TSPSolution(
                route=list(range(len(nodes_in_route_order))),
                distance=distance,
            )
            unused_nodes = [
                _with_type(n, NodeType.PICKUP)
                for i, n in enumerate(pickups)
                if i != best.pickup_index
            ]
            pickup_detour_delta = max(0.0, best.delta)
        else:
            unused_nodes = [_with_type(n, NodeType.PICKUP) for n in pickups]
            pickup_detour_delta = 0.0

        return CoolTspSolution(
            solution=solution,
            nodes=nodes_in_route_order,
            unused_nodes=unused_nodes,
            pickup_detour_delta=pickup_detour_delta,
        )
