"""Tests for mytsp solver."""

import pytest

from mytsp import NaiveSolver, Node, TSPInstance
from mytsp.cool_solver import (
    CoolSolver,
    DetourEntry,
    _build_detour_accelerator,
    _compute_load_profile,
    _find_best_insertion,
    _insert_pickup,
    _select_best_pickup,
)
from mytsp.models import CoolTspProblem, NodeType
from mytsp.solver import NearestNeighborSolver, Simple2PointSolver


def test_naive_solver_returns_solution() -> None:
    """NaiveSolver.solve returns a valid TSPSolution."""
    instance = TSPInstance(
        nodes=[
            Node(x=0.0, y=0.0),
            Node(x=3.0, y=0.0),
            Node(x=3.0, y=4.0),
        ]
    )
    solver = NaiveSolver()
    solution = solver.solve(instance)
    assert len(solution.route) == 3
    assert set(solution.route) == {0, 1, 2}
    assert solution.distance >= 0


def test_naive_solver_two_nodes() -> None:
    """Two nodes: route [0,1], closed tour distance is 2 * Euclidean."""
    instance = TSPInstance(nodes=[Node(x=0.0, y=0.0), Node(x=3.0, y=4.0)])
    solver = NaiveSolver()
    solution = solver.solve(instance)
    assert solution.route == [0, 1]
    assert solution.distance == pytest.approx(10.0)  # 5 + 5 round trip


def test_naive_solver_triangle_tour_length() -> None:
    """Triangle (0,0)-(3,0)-(3,4) closed tour length 12."""
    instance = TSPInstance(
        nodes=[
            Node(x=0.0, y=0.0),
            Node(x=3.0, y=0.0),
            Node(x=3.0, y=4.0),
        ]
    )
    solver = NaiveSolver()
    solution = solver.solve(instance)
    # 3 + 4 + 5 = 12
    assert solution.distance == pytest.approx(12.0)


def test_nearest_neighbor_solver_triangle_tour_length() -> None:
    """Triangle (0,0)-(3,0)-(3,4) closed tour length 12."""
    instance = TSPInstance(
        nodes=[
            Node(x=0.0, y=0.0),
            Node(x=3.0, y=0.0),
            Node(x=3.0, y=4.0),
        ]
    )
    solver = NearestNeighborSolver()
    solution = solver.solve(instance)
    # 3 + 4 + 5 = 12
    assert solution.distance == pytest.approx(12.0)


def test_2p_solver_triangle_tour_length() -> None:
    """Triangle (0,0)-(3,0)-(3,4) closed tour: no 2-opt improvement, distance 12."""
    instance = TSPInstance(
        nodes=[
            Node(x=0.0, y=0.0),
            Node(x=3.0, y=0.0),
            Node(x=3.0, y=4.0),
        ]
    )
    solver = Simple2PointSolver()
    solution = solver.solve(instance)
    assert solution.distance == pytest.approx(12.0)


# L-shaped 5 points: nearest-neighbor creates a suboptimal tour that 2-opt can improve
L_SHAPE_5 = [
    Node(x=0.0, y=0.0),
    Node(x=2.0, y=0.0),
    Node(x=2.0, y=2.0),
    Node(x=4.0, y=2.0),
    Node(x=4.0, y=4.0),
]


def test_nearest_neighbor_solver_lshape_tour_length() -> None:
    """L-shape 5 points: nearest-neighbor produces suboptimal tour with crossing."""
    instance = TSPInstance(nodes=L_SHAPE_5)
    solution = NearestNeighborSolver().solve(instance)
    assert solution.distance == pytest.approx(13.65685424949238)


def test_2p_solver_improves_over_nn_on_lshape() -> None:
    """2-opt improves over nearest-neighbor on L-shape by uncrossing edges."""
    instance = TSPInstance(nodes=L_SHAPE_5)
    nn_sol = NearestNeighborSolver().solve(instance)
    two_p_sol = Simple2PointSolver().solve(instance)
    assert two_p_sol.distance <= nn_sol.distance
    assert two_p_sol.distance < nn_sol.distance  # strictly better
    assert two_p_sol.distance == pytest.approx(12.48528137423857)


def test_cool_solver_delivery_only() -> None:
    """CoolSolver solves delivery part via 2-opt; start + deliveries in tour."""
    deliveries = [
        Node(x=0.0, y=0.0, demand=1),
        Node(x=3.0, y=0.0, demand=2),
        Node(x=3.0, y=4.0, demand=1),
    ]
    problem = CoolTspProblem(
        deliveries=deliveries,
        pickups=[],
        vehicle_capacity=100.0,
    )
    result = CoolSolver(Simple2PointSolver()).solve(problem)
    assert len(result.nodes) == 4  # start + 3 deliveries
    assert len(result.solution.route) == 4
    assert set(result.solution.route) == {0, 1, 2, 3}
    assert result.solution.distance > 0
    assert any(n.node_type == NodeType.START for n in result.nodes)
    assert result.unused_nodes == []


def test_cool_solver_respects_capacity_subset() -> None:
    """CoolSolver selects only deliveries that fit in capacity (greedy by demand asc)."""
    deliveries = [
        Node(x=0.0, y=0.0, demand=1),
        Node(x=3.0, y=0.0, demand=2),
        Node(x=3.0, y=4.0, demand=1),
    ]
    problem = CoolTspProblem(
        deliveries=deliveries,
        pickups=[],
        vehicle_capacity=2.5,
    )
    result = CoolSolver(Simple2PointSolver()).solve(problem)
    assert len(result.nodes) == 3  # start + 2 deliveries
    assert sum(n.demand for n in result.nodes) <= problem.vehicle_capacity
    assert len(result.solution.route) == 3
    assert set(result.solution.route) == {0, 1, 2}
    assert any(n.node_type == NodeType.START for n in result.nodes)


# --- Pickup detour helpers (unit tests) ---


def test_build_detour_accelerator_sorting() -> None:
    """Entries sorted ascending by delta; delta = detour - base."""
    pickup = Node(x=1.0, y=1.0)
    # Route: (0,0) -> (3,0) -> (3,4) -> back to (0,0)
    route = [
        Node(x=0.0, y=0.0),
        Node(x=3.0, y=0.0),
        Node(x=3.0, y=4.0),
    ]
    acc = _build_detour_accelerator(pickup, route)
    assert len(acc) == 3  # 3 edges including closing
    for i in range(len(acc) - 1):
        assert acc[i].delta <= acc[i + 1].delta
    # Each entry has valid edge_index in [0, 1, 2]
    for e in acc:
        assert 0 <= e.edge_index < 3
        assert isinstance(e, DetourEntry)


def test_compute_load_profile_forward() -> None:
    """Direct load at each point: start with total, subtract each delivery."""
    # Depot (0) + two deliveries with demand 5 and 3
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=5),
        Node(x=2.0, y=0.0, demand=3),
    ]
    profile = _compute_load_profile(route)
    assert len(profile) == 3
    assert profile[0][0] == 8.0  # total at depot
    assert profile[1][0] == 3.0  # after delivering 5
    assert profile[2][0] == 0.0  # after delivering 3


def test_compute_load_profile_reverse() -> None:
    """Reverse load computed independently with varied demands."""
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=8),
        Node(x=2.0, y=0.0, demand=2),
    ]
    profile = _compute_load_profile(route)
    # reverse_load[0] = total = 10
    assert profile[0][1] == 10.0
    # reverse_load[2] = 10 - demand[2] = 8
    assert profile[2][1] == 8.0
    # reverse_load[1] = 8 - demand[1] = 0
    assert profile[1][1] == 0.0


def test_compute_load_profile_partial_capacity() -> None:
    """Vehicle capacity > total demand; both direction profiles reflect loads."""
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=1),
        Node(x=2.0, y=0.0, demand=2),
    ]
    profile = _compute_load_profile(route)
    assert profile[0] == (3.0, 3.0)
    # direct_load[1]=2 (after delivering 1); reverse_load[1]=0 (after d2,d1 in reverse)
    assert profile[1] == (2.0, 0.0)
    # direct_load[2]=0; reverse_load[2]=1 (total - demand[2])
    assert profile[2] == (0.0, 1.0)


def test_find_best_insertion_direct() -> None:
    """Pickup fits at cheapest edge in direct direction."""
    pickup = Node(x=1.0, y=1.0, demand=2.0)
    # Route: depot, d1(demand 1), d2(demand 1). Total 2. Capacity 10.
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=3.0, y=0.0, demand=1),
        Node(x=3.0, y=4.0, demand=1),
    ]
    profile = _compute_load_profile(route)
    acc = _build_detour_accelerator(pickup, route)
    cand = _find_best_insertion(pickup, 0, acc, profile, capacity=10.0)
    assert cand is not None
    assert cand.pickup is pickup
    assert cand.reverse is False
    assert cand.delta >= 0


def test_find_best_insertion_reverse_only() -> None:
    """Cheapest edge only fits in reverse; first feasible candidate uses reverse."""
    # Route: depot, d1(demand 8), d2(demand 1). Total 9. Capacity 10, pickup 2.
    # Edge 0: direct_load=9, 9+2=11>10; reverse_load[1]=8, 8+2=10<=10 -> reverse fits.
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=0.5, y=0.0, demand=8),
        Node(x=2.0, y=0.0, demand=1),
    ]
    pickup = Node(x=0.3, y=0.0, demand=2.0)
    profile = _compute_load_profile(route)
    acc = _build_detour_accelerator(pickup, route)
    cand = _find_best_insertion(pickup, 0, acc, profile, capacity=10.0)
    assert cand is not None
    assert cand.pickup is pickup
    # Edge 0 is cheapest; direct fails (9+2>10), reverse fits -> reverse=True
    assert cand.reverse is True


def test_find_best_insertion_no_capacity() -> None:
    """No edge has capacity for pickup; returns None."""
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=5),
        Node(x=2.0, y=0.0, demand=5),
    ]
    pickup = Node(x=1.0, y=1.0, demand=100.0)
    profile = _compute_load_profile(route)
    acc = _build_detour_accelerator(pickup, route)
    cand = _find_best_insertion(pickup, 0, acc, profile, capacity=10.0)
    assert cand is None


def test_select_best_pickup_multiple() -> None:
    """Among several pickups, the one with smallest feasible delta wins."""
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=1),
        Node(x=2.0, y=0.0, demand=1),
    ]
    # Two pickups: one close (small delta), one far (large delta). Both fit.
    near = Node(x=0.5, y=0.0, demand=1.0)
    far = Node(x=10.0, y=10.0, demand=1.0)
    best = _select_best_pickup([far, near], route, capacity=10.0)
    assert best is not None
    assert best.pickup is near
    assert best.delta < 5.0


def test_insert_pickup_direct() -> None:
    """Pickup node appears at correct position with NodeType PICKUP."""
    route = [
        Node(x=0.0, y=0.0, demand=0),
        Node(x=1.0, y=0.0, demand=1),
        Node(x=2.0, y=0.0, demand=1),
    ]
    pickup = Node(x=0.5, y=0.0, demand=1.0)
    out = _insert_pickup(route, pickup, edge_index=0, reverse=False)
    assert len(out) == 4
    assert out[0] == route[0]
    assert out[1].node_type == NodeType.PICKUP
    assert out[1].x == pickup.x and out[1].y == pickup.y
    assert out[2] == route[1]
    assert out[3] == route[2]


def test_insert_pickup_reverse() -> None:
    """Route is reversed and pickup inserted at correct position."""
    route = [
        Node(x=0.0, y=0.0, demand=0, name="depot"),
        Node(x=1.0, y=0.0, demand=1, name="d1"),
        Node(x=2.0, y=0.0, demand=1, name="d2"),
    ]
    pickup = Node(x=1.5, y=0.0, demand=1.0)
    out = _insert_pickup(route, pickup, edge_index=0, reverse=True)
    # Reversed: [depot, d2, d1]. Edge 0 -> edge 2. Pickup between d1 and depot.
    assert len(out) == 4
    assert out[0] == route[0]
    assert out[1].name == "d2"
    assert out[2].name == "d1"
    assert out[3].node_type == NodeType.PICKUP


# --- CoolSolver integration with pickups ---


def test_cool_solver_with_pickup() -> None:
    """End-to-end: one pickup in route, unused_nodes and distance include detour."""
    deliveries = [
        Node(x=0.0, y=0.0, demand=1),
        Node(x=3.0, y=0.0, demand=1),
        Node(x=3.0, y=4.0, demand=1),
    ]
    pickups = [Node(x=1.5, y=0.5, demand=1.0)]
    problem = CoolTspProblem(
        deliveries=deliveries,
        pickups=pickups,
        vehicle_capacity=10.0,
    )
    result = CoolSolver(Simple2PointSolver()).solve(problem)
    assert len(result.nodes) == 5  # start + 3 deliveries + 1 pickup
    assert sum(1 for n in result.nodes if n.node_type == NodeType.PICKUP) == 1
    assert len(result.unused_nodes) == 0
    assert result.pickup_detour_delta >= 0
    assert result.solution.distance > 0


def test_cool_solver_no_feasible_pickup() -> None:
    """Pickups exist but none fit capacity; result is delivery-only."""
    deliveries = [
        Node(x=0.0, y=0.0, demand=5),
        Node(x=3.0, y=0.0, demand=5),
    ]
    pickups = [Node(x=1.0, y=1.0, demand=100.0)]  # cannot fit
    problem = CoolTspProblem(
        deliveries=deliveries,
        pickups=pickups,
        vehicle_capacity=10.0,
    )
    result = CoolSolver(Simple2PointSolver()).solve(problem)
    assert len(result.nodes) == 3  # start + 2 deliveries, no pickup
    assert sum(1 for n in result.nodes if n.node_type == NodeType.PICKUP) == 0
    assert len(result.unused_nodes) == 1
    assert result.pickup_detour_delta == 0.0
