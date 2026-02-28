#!/usr/bin/env python3
"""Generate CoolTsp benchmark files for load_cool_bench.

Points use uncorrelated 2D uniform random distribution.
Demands are drawn from a normal distribution and are independent of delivery location.
"""

import argparse
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CoolTsp instance: uniform 2D points, normal demand.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output file path (e.g. bench/my_instance.txt)",
    )
    parser.add_argument(
        "-n",
        "--customers",
        type=int,
        default=101,
        help="Number of customers including depot (default: 101)",
    )
    parser.add_argument(
        "--capacity",
        type=float,
        default=200.0,
        help="Vehicle capacity (default: 200)",
    )
    parser.add_argument(
        "--vehicles",
        type=int,
        default=25,
        help="Number of vehicles (default: 25)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=100.0,
        help="Half-range for x,y: points in [-scale, scale] (default: 100)",
    )
    parser.add_argument(
        "--demand-mean",
        type=float,
        default=20.0,
        help="Mean demand (default: 20)",
    )
    parser.add_argument(
        "--demand-std",
        type=float,
        default=10.0,
        help="Std dev of demand (default: 10)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Instance name in file header (default: output stem)",
    )
    args = parser.parse_args()

    n = args.customers
    if n < 2:
        raise SystemExit("Need at least 2 nodes (depot + one customer).")

    rng = np.random.default_rng(args.seed)

    # Depot at origin, demand 0
    depot = (0.0, 0.0, 0.0)

    # Uncorrelated 2D uniform: x and y independent U(-scale, scale)
    x = rng.uniform(-args.scale, args.scale, size=n - 1)
    y = rng.uniform(-args.scale, args.scale, size=n - 1)

    # Demands: normal, independent of position
    raw_demand = rng.normal(args.demand_mean, args.demand_std, size=n - 1)
    demand = np.maximum(raw_demand, 1.0)

    rows: list[tuple[int, float, float, float]] = [
        (0, depot[0], depot[1], depot[2]),
    ]
    for i in range(n - 1):
        rows.append((i + 1, float(x[i]), float(y[i]), float(demand[i])))

    name = args.name or args.output.stem
    lines = [
        name,
        "",
        "VEHICLE",
        "NUMBER     CAPACITY",
        f"  {args.vehicles}         {int(args.capacity)}",
        "",
        "CUSTOMER",
        "CUST NO.  XCOORD.   YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE   TIME",
        "",
    ]
    for cust_no, xi, yi, d in rows:
        demand_int = 0 if cust_no == 0 else max(1, int(round(d)))
        tail = "          0       1236         90"
        lines.append(f"  {cust_no:3d}    {xi:8.2f}   {yi:8.2f}   {demand_int:5d}  {tail}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({n} nodes, capacity {args.capacity}, seed {args.seed})")


if __name__ == "__main__":
    main()
