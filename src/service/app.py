"""FastAPI application factory."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from service.logging import configure_logging, get_logger
from service.routes import router
from service.settings import get_settings

SERVICE_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Startup: load settings, configure logging, set app state."""
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.version = SERVICE_VERSION
    app.state.start_time = time.monotonic()
    yield
    # shutdown: nothing to tear down


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TSP Service",
        description="Microservice for CoolTsp: delivery/pickup routing with capacity.",
        version=SERVICE_VERSION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "tsp", "description": "CoolTsp solve and health endpoints"},
        ],
    )
    app.include_router(router, tags=["tsp"])

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        log = get_logger()
        log.exception("unhandled_exception")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
