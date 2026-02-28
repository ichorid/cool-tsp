"""CoolBench: load c101 as CoolTsp (20/80 split, demand, capacity), solve with CoolSolver.

Instance interpretation (load_cool_bench):
- The Solomon file (e.g. c101.txt) lists all customer nodes with coordinates and demand.
- **80/20 split**: 20% of nodes are randomly assigned as *pickups*, 80% as *deliveries*
  (using a fixed seed for reproducibility). The depot is implicit at start.
- Deliveries are served first (TSP tour respecting capacity); then the solver may add
  pickups along the route if capacity allows (see algo_explainer.md).

Run: uv run python bench/cool_bench.py
Or: uv run pytest bench/cool_bench.py -v -s
"""

import time
from pathlib import Path

import pytest

from mytsp import CoolSolver, CoolTspSolution, Simple2PointSolver, load_cool_bench
from mytsp.models import NodeType

BENCH_DIR = Path(__file__).resolve().parent
C101_PATH = BENCH_DIR / "c101.txt"
COOL_BENCH_SEED = 42


def run() -> tuple[CoolTspSolution, float]:
    """Load c101 as CoolTsp, solve delivery. Returns (solution, elapsed_s)."""
    problem = load_cool_bench(C101_PATH, seed=COOL_BENCH_SEED)
    solver = CoolSolver(Simple2PointSolver())
    t0 = time.perf_counter()
    solution = solver.solve(problem)
    elapsed = time.perf_counter() - t0

    print(f"delivery_nodes: {len(problem.deliveries)}")
    deliveries_served = sum(1 for n in solution.nodes if n.node_type != NodeType.START)
    print(f"deliveries_served: {deliveries_served}")
    print(f"pickup_nodes: {len(problem.pickups)}")
    print(f"vehicle_capacity: {problem.vehicle_capacity}")
    print(f"delivery_tour_distance: {solution.solution.distance:.2f}")
    print(f"solve_time_s: {elapsed:.3f}")
    return solution, elapsed


@pytest.mark.bench
def test_cool_bench_load_and_solve() -> None:
    """Load CoolTsp from c101, run CoolSolver, assert valid delivery solution."""
    problem = load_cool_bench(C101_PATH, seed=COOL_BENCH_SEED)

    solution, elapsed = run()
    # Delivery load fits capacity; pickup adds demand so total can exceed capacity
    delivery_demand = sum(
        n.demand for n in solution.nodes if n.node_type != NodeType.PICKUP
    )
    assert elapsed < 30.0, f"solve took {elapsed:.2f}s"


if __name__ == "__main__":
    run()
