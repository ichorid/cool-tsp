"""I/O utilities for loading TSP instance data."""

from pathlib import Path

from mytsp.models import Node, TSPInstance


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
    while i < len(lines) and (not lines[i].strip() or "CUST NO" in lines[i].upper() or "XCOORD" in lines[i].upper()):
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
        except (ValueError, IndexError):
            continue

    if len(rows) < 2:
        raise ValueError(f"Need at least 2 nodes, got {len(rows)}")

    # Sort by customer index so nodes[i] is customer i
    rows.sort(key=lambda r: r[0])
    nodes = [Node(x=x, y=y, name=str(cust_no)) for cust_no, x, y in rows]
    return TSPInstance(nodes=nodes)
