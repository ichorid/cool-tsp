"""FastAPI application factory."""

from fastapi import FastAPI

from service.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TSP Service",
        description="Microservice for solving Travelling Salesman Problem instances",
        version="0.1.0",
    )
    app.include_router(router, tags=["tsp"])
    return app


app = create_app()
