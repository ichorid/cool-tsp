"""Tests for mytsp solver."""

import pytest

from mytsp import NaiveSolver, Node, TSPInstance


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
