"""Tests for mytsp models."""

import pytest

from mytsp.models import Node, TSPInstance, TSPSolution


def test_node_creation() -> None:
    """Node accepts x, y and optional name."""
    n = Node(x=0.0, y=0.0)
    assert n.x == 0.0 and n.y == 0.0 and n.name is None

    n2 = Node(x=1.0, y=2.0, name="A")
    assert n2.name == "A"


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
