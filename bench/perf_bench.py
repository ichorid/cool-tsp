"""Performance benchmark using Solomon-format test data.

Run standalone: uv run python bench/perf_bench.py
Or with pytest: uv run pytest bench/ -v -s
"""

import time
from pathlib import Path

from mytsp import NaiveSolver, load_solomon
from mytsp.models import TSPInstance, TSPSolution

# Solomon data file next to this script
BENCH_DIR = Path(__file__).resolve().parent
C101_PATH = BENCH_DIR / "c101.txt"


def run() -> tuple[TSPInstance, TSPSolution, float]:
    """Load c101, solve with NaiveSolver, print stats. Returns (instance, solution, elapsed_s)."""
    instance = load_solomon(C101_PATH)
    solver = NaiveSolver()
    t0 = time.perf_counter()
    solution = solver.solve(instance)
    elapsed = time.perf_counter() - t0

    print(f"nodes: {len(instance.nodes)}")
    print(f"distance: {solution.distance:.2f}")
    print(f"solve_time_s: {elapsed:.3f}")
    return instance, solution, elapsed


def test_perf_bench_c101_load_and_solve() -> None:
    """Pytest entrypoint: run benchmark and assert valid solution."""
    instance, solution, elapsed = run()
    assert len(instance.nodes) == 101
    assert instance.nodes[0].x == 40.0 and instance.nodes[0].y == 50.0
    assert len(solution.route) == 101
    assert set(solution.route) == set(range(101))
    assert solution.distance > 0
    assert elapsed < 10.0, f"solve took {elapsed:.2f}s"


if __name__ == "__main__":
    run()
