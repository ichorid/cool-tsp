"""Tests for mytsp models."""

import pytest

from mytsp.models import CoolTspProblem, Node, TSPInstance, TSPSolution


def test_node_creation() -> None:
    """Node accepts x, y and optional name."""
    n = Node(x=0.0, y=0.0)
    assert n.x == 0.0 and n.y == 0.0 and n.name is None

    n2 = Node(x=1.0, y=2.0, name="A")
    assert n2.name == "A"


def test_node_demand_default_and_explicit() -> None:
    """Node has demand; default is 0 when omitted, can be set explicitly."""
    n = Node(x=0.0, y=0.0)
    assert n.demand == 0

    n2 = Node(x=0.0, y=0.0, demand=10)
    assert n2.demand == 10


def test_tsp_instance_requires_at_least_two_nodes() -> None:
    """TSPInstance validates min_length=2 for nodes."""
    TSPInstance(nodes=[Node(x=0, y=0), Node(x=1, y=1)])
    with pytest.raises(ValueError):
        TSPInstance(nodes=[Node(x=0, y=0)])


def test_tsp_solution_route_and_distance() -> None:
    """TSPSolution stores route and non-negative distance."""
    sol = TSPSolution(route=[0, 1, 2], distance=10.5)
    assert sol.route == [0, 1, 2]
    assert sol.distance == 10.5

    with pytest.raises(ValueError):
        TSPSolution(route=[0], distance=-1.0)


def test_cool_tsp_problem_creation() -> None:
    """CoolTspProblem stores start, deliveries, pickups, and vehicle_capacity."""
    d1 = Node(x=0.0, y=0.0, demand=5)
    d2 = Node(x=1.0, y=1.0, demand=10)
    p1 = Node(x=2.0, y=2.0, demand=3)
    problem = CoolTspProblem(
        deliveries=[d1, d2],
        pickups=[p1],
        vehicle_capacity=200.0,
    )
    assert problem.start.x == 0.0 and problem.start.y == 0.0
    assert len(problem.deliveries) == 2
    assert len(problem.pickups) == 1
    assert problem.vehicle_capacity == 200.0
