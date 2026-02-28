"""Solver interface and reference implementations."""

from abc import ABC, abstractmethod

from mytsp.models import TSPInstance, TSPSolution


class Solver(ABC):
    """Abstract base class for TSP solvers."""

    @abstractmethod
    def solve(self, instance: TSPInstance) -> TSPSolution:
        """Solve the given TSP instance and return a solution."""
        ...


class NaiveSolver(Solver):
    """Reference solver: brute-force for tiny instances (template only)."""

    def solve(self, instance: TSPInstance) -> TSPSolution:
        """Return a trivial solution (first node only or minimal stub)."""
        if len(instance.nodes) < 2:
            return TSPSolution(route=[0], distance=0.0)
        # Placeholder: visit nodes in given order and compute distance
        route = list(range(len(instance.nodes)))
        distance = 0.0
        for i in range(len(route)):
            j = (i + 1) % len(route)
            a, b = instance.nodes[route[i]], instance.nodes[route[j]]
            distance += ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        return TSPSolution(route=route, distance=distance)
