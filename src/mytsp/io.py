"""I/O utilities for loading TSP instance data."""

import random
from pathlib import Path

from mytsp.models import CoolTspProblem, Node, TSPInstance


def load_solomon(path: Path | str) -> TSPInstance:
    """Load a Solomon-format (VRPTW-style) file into a TSP instance.

    Parses the CUSTOMER section and builds nodes from CUST NO., XCOORD., YCOORD.
    Nodes are ordered by customer index so that nodes[i] corresponds to customer i.
    """
    path = Path(path)
    text = path.read_text()
    lines = text.splitlines()

    # Find CUSTOMER section
    i = 0
    while i < len(lines) and "CUSTOMER" not in lines[i]:
        i += 1
    if i >= len(lines):
        raise ValueError("No CUSTOMER section found")
    i += 1  # skip "CUSTOMER" line

    # Skip column header and any blank line
    def skip_header(j: int) -> bool:
        line = lines[j].strip()
        return not line or "CUST NO" in line.upper() or "XCOORD" in line.upper()

    while i < len(lines) and skip_header(i):
        i += 1

    # Parse data lines: cust_no, x, y (first three numeric fields)
    rows: list[tuple[int, float, float]] = []
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            first = parts[0]
            if not first.lstrip("-").isdigit():
                continue
            cust_no = int(first)
            x = float(parts[1])
            y = float(parts[2])
            rows.append((cust_no, x, y))
        except ValueError, IndexError:
            continue

    if len(rows) < 2:
        raise ValueError(f"Need at least 2 nodes, got {len(rows)}")

    # Sort by customer index so nodes[i] is customer i
    rows.sort(key=lambda r: r[0])
    nodes = [Node(x=x, y=y, name=str(cust_no)) for cust_no, x, y in rows]
    return TSPInstance(nodes=nodes)


def load_cool_bench(path: Path | str, seed: int = 421) -> CoolTspProblem:
    """Load a Solomon-format (VRPTW-style) file as a CoolTsp problem.

    Parses VEHICLE section for CAPACITY and CUSTOMER section for CUST NO., XCOORD.,
    YCOORD., DEMAND. Nodes get demand set from the DEMAND column. Then 20% of nodes
    are randomly assigned to pickups and 80% to deliveries (using the given seed for
    reproducibility).
    """
    path = Path(path)
    text = path.read_text()
    lines = text.splitlines()

    # Parse VEHICLE section: line after "NUMBER CAPACITY" has e.g. "  25  200"
    vehicle_capacity = 0.0
    for idx, line in enumerate(lines):
        if "NUMBER" in line.upper() and "CAPACITY" in line.upper():
            if idx + 1 < len(lines):
                parts = lines[idx + 1].split()
                nums = [float(p) for p in parts if _is_numeric(p)]
                if len(nums) >= 2:
                    vehicle_capacity = nums[1]
            break

    # Find CUSTOMER section
    i = 0
    while i < len(lines) and "CUSTOMER" not in lines[i]:
        i += 1
    if i >= len(lines):
        raise ValueError("No CUSTOMER section found")
    i += 1
    while i < len(lines) and (
        not lines[i].strip()
        or "CUST NO" in lines[i].upper()
        or "XCOORD" in lines[i].upper()
    ):
        i += 1

    # Parse data lines: cust_no, x, y, demand
    rows: list[tuple[int, float, float, float]] = []
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            first = parts[0]
            if not first.lstrip("-").isdigit():
                continue
            cust_no = int(first)
            x = float(parts[1])
            y = float(parts[2])
            demand = float(parts[3])
            rows.append((cust_no, x, y, demand))
        except ValueError, IndexError:
            continue

    if len(rows) < 1:
        raise ValueError("Need at least 1 node for CoolTsp, got 0")

    rows.sort(key=lambda r: r[0])
    nodes = [
        Node(x=x, y=y, name=str(cust_no), demand=demand) for cust_no, x, y, demand in rows
    ]

    # 20% pickups, 80% deliveries (fixed seed)
    rng = random.Random(seed)
    n = len(nodes)
    indices = list(range(n))
    rng.shuffle(indices)
    n_pickup = max(0, int(n * 0.2))
    deliveries = [nodes[i] for i in indices[n_pickup:]]
    pickups = [nodes[i] for i in indices[:n_pickup]]

    return CoolTspProblem(
        deliveries=deliveries,
        pickups=pickups,
        vehicle_capacity=vehicle_capacity,
    )


def _is_numeric(s: str) -> bool:
    s = s.strip()
    if not s:
        return False
    return s.lstrip("-").replace(".", "", 1).isdigit()
