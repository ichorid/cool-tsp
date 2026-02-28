# Build stage: install dependencies with uv
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies (no dev group)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and readme (hatchling needs README.md for metadata)
COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

# Runtime stage
FROM python:3.14-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/false --create-home app

# Copy virtual environment from builder (project is installed inside it)
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000

CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
