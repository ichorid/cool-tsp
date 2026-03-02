
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ichorid/cool-tsp)

# cool-tsp

Travelling Salesman Problem (TSP) library and FastAPI microservice. Exercise repo demonstrating modern Python tooling (uv, Python 3.14, ruff, mypy) and deployment (Docker, GitHub Actions).

**Algorithm reference:** [algo_explainer.md](algo_explainer.md)

## Quickstart

```bash
# Clone and install
git clone https://github.com/your-org/cool-tsp.git && cd cool-tsp
uv sync --all-groups
```

**Run the benchmark** — load a Solomon-format instance (e.g. c101), solve with CoolSolver:

```bash
uv run python bench/cool_bench.py
```

**Use the library** — solve a small TSP in Python:

```python
from mytsp import Node, TSPInstance, Simple2PointSolver

instance = TSPInstance(nodes=[Node(x=0, y=0), Node(x=3, y=4), Node(x=1, y=1), Node(x=2, y=2)])
result = Simple2PointSolver().solve(instance)
print(result.route, result.distance)  # e.g. [0, 2, 3, 1, 0], 8.48...
```

**Or run the API** — start the service and POST a problem:

```bash
uv run uvicorn service.app:app --reload --host 0.0.0.0 --port 8000
# POST http://localhost:8000/v1/solve with JSON: {"deliveries": [{"x": 0, "y": 0}, {"x": 3, "y": 4}, ...], "vehicle_capacity": 100}
```

See [Setup](#setup) and [Running the service](#running-the-service) for details.

## Structure

- **`mytsp`** — Python library for TSP: data models, solver interface, and implementations.
- **`service`** — FastAPI microservice that accepts TSP instances and returns solutions via HTTP.
- **`bench`** — Benchmark instances (e.g. `c101.txt`) and `gen_cool_bench.py` to generate Solomon-format CoolTsp files.
- **[`algo_explainer.md`](algo_explainer.md)** — CoolSolver pickup detour algorithm reference with mermaid diagrams.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.14

## Setup

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create venv
uv sync --all-groups
```

## Jupyter demo

Run the TSP demo notebook (uses the `viz` dependency group; included in `uv sync --all-groups`):

```bash
uv run jupyter notebook bench/tsp_demo.ipynb
```

Or with JupyterLab: `uv run jupyter lab bench/tsp_demo.ipynb`

## Development

```bash
# Run linter and formatter
uv run ruff check src tests && uv run ruff format src tests

# Type check
uv run mypy src

# Tests
uv run pytest

# Benchmarks (optional; run bench scripts with pytest)
uv run pytest bench/ -v -s -m bench

# Install pre-commit hooks (optional)
uv run pre-commit install
```

## Running the service

```bash
uv run uvicorn service.app:app --reload --host 0.0.0.0 --port 8000
```

- **GET /v1/health** — Health check.
- **POST /v1/solve** — Solve a CoolTsp instance. Body: `{"deliveries": [{"x": 0, "y": 0}, {"x": 3, "y": 4}, ...], "vehicle_capacity": 100}` (optional: `start`, `pickups`, `solver`). Response: `{"solution": {"route": [0, 1, ...], "distance": 12.5}, "nodes": [...], "unused_nodes": [...], "pickup_detour_delta": 0.0}`.

## Benchmark generator

The `bench/gen_cool_bench.py` script generates Solomon-format instance files compatible with `load_cool_bench` (CoolTsp pickup/delivery problems):

- **Points** — **Uncorrelated 2D uniform**: x and y independent Uniform(−scale, scale) around the origin.
- **Demands** — Drawn from a **normal distribution** and **independent** of delivery location (no correlation between position and demand).

Output format matches `c101.txt` (VEHICLE section with NUMBER/CAPACITY, CUSTOMER section with CUST NO., XCOORD., YCOORD., DEMAND).

```bash
# Default: 101 customers, capacity 200, 25 vehicles, seed 42
uv run python bench/gen_cool_bench.py bench/my_instance.txt

# Custom size and parameters
uv run python bench/gen_cool_bench.py -n 50 --capacity 200 --scale 80 \
  --demand-mean 15 --demand-std 8 --seed 123 bench/uniform_50.txt
```

| Option | Default | Description |
|--------|---------|-------------|
| `output` | (required) | Output file path |
| `-n`, `--customers` | 101 | Number of customers including depot |
| `--capacity` | 200 | Vehicle capacity |
| `--vehicles` | 25 | Number of vehicles |
| `--scale` | 100 | Half-range for x,y: points in [−scale, scale] |
| `--demand-mean` | 20 | Mean demand |
| `--demand-std` | 10 | Standard deviation of demand |
| `--seed` | 42 | Random seed |
| `--name` | output stem | Instance name in file header |

Load a generated file in Python: `load_cool_bench(Path("bench/my_instance.txt"), seed=42)`.

## Docker

```bash
docker build -t cool-tsp .
docker run -p 8000:8000 cool-tsp
```

## CI/CD

- **Push to `main`** — Runs ruff, mypy, and pytest (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).
- **Push to `release`** — Builds the Docker image and pushes it to GitHub Container Registry (ghcr.io) (see [.github/workflows/release.yml](.github/workflows/release.yml)).

## License

MIT
