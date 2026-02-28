# cool-tsp

Travelling Salesman Problem (TSP) library and FastAPI microservice. Exercise repo demonstrating modern Python tooling (uv, Python 3.14, ruff, mypy) and deployment (Docker, GitHub Actions).

## Structure

- **`mytsp`** — Python library for TSP: data models, solver interface, and implementations.
- **`service`** — FastAPI microservice that accepts TSP instances and returns solutions via HTTP.

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

## Development

```bash
# Run linter and formatter
uv run ruff check src tests && uv run ruff format src tests

# Type check
uv run mypy src

# Tests
uv run pytest

# Install pre-commit hooks (optional)
uv run pre-commit install
```

## Running the service

```bash
uv run uvicorn service.app:app --reload --host 0.0.0.0 --port 8000
```

- **GET /health** — Health check.
- **POST /solve** — Solve a TSP instance. Body: `{"nodes": [{"x": 0, "y": 0}, {"x": 3, "y": 4}, ...]}`. Response: `{"route": [0, 1, ...], "distance": 12.5}`.

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
