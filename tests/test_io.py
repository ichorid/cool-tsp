"""Tests for I/O loaders."""

from pathlib import Path

from mytsp.io import load_cool_bench

BENCH_DIR = Path(__file__).resolve().parent.parent / "bench"
C101_PATH = BENCH_DIR / "c101.txt"


def test_load_cool_bench_capacity_and_counts() -> None:
    """c101 load: capacity 200, 101 nodes, 20% pickups and 80% deliveries."""
    problem = load_cool_bench(C101_PATH, seed=42)
    assert problem.vehicle_capacity == 200
    assert len(problem.deliveries) + len(problem.pickups) == 101
    assert len(problem.pickups) == 20
    assert len(problem.deliveries) == 81


def test_load_cool_bench_demand_on_nodes() -> None:
    """Nodes loaded from c101 have demand set from DEMAND column."""
    problem = load_cool_bench(C101_PATH, seed=42)
    # c101 has non-zero demands on many nodes
    total_demand = sum(n.demand for n in problem.deliveries) + sum(
        n.demand for n in problem.pickups
    )
    assert total_demand > 0


def test_load_cool_bench_reproducible_with_same_seed() -> None:
    """Same seed produces identical delivery/pickup split."""
    p1 = load_cool_bench(C101_PATH, seed=42)
    p2 = load_cool_bench(C101_PATH, seed=42)
    assert len(p1.deliveries) == len(p2.deliveries)
    assert len(p1.pickups) == len(p2.pickups)
    # Same nodes assigned to delivery/pickup with same seed
    for a, b in zip(p1.deliveries, p2.deliveries, strict=True):
        assert a.x == b.x and a.y == b.y and a.demand == b.demand
    for a, b in zip(p1.pickups, p2.pickups, strict=True):
        assert a.x == b.x and a.y == b.y and a.demand == b.demand
