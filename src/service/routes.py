"""API route handlers."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from mytsp import (
    CoolSolver,
    CoolTspProblem,
    CoolTspSolution,
    NaiveSolver,
    NearestNeighborSolver,
    Simple2PointSolver,
    Solver,
)
from service.logging import get_logger
from service.schemas import SolveRequest, SolverStrategy
from service.settings import Settings, get_settings

router = APIRouter(prefix="/v1")

log = get_logger()


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    """Health check endpoint."""
    start_time: float | None = getattr(request.app.state, "start_time", None)
    version: str | None = getattr(request.app.state, "version", None)
    uptime_s = None if start_time is None else time.monotonic() - start_time

    return {
        "status": "ok",
        "version": version,
        "uptime_s": uptime_s,
    }


def _select_strategy(
    requested: SolverStrategy | None, settings: Settings
) -> SolverStrategy:
    if requested is not None:
        return requested
    try:
        return SolverStrategy(settings.default_solver)
    except ValueError as exc:  # pragma: no cover
        raise RuntimeError(
            f"Invalid TSP_DEFAULT_SOLVER: {settings.default_solver!r}"
        ) from exc


def _build_solver(strategy: SolverStrategy, settings: Settings) -> Solver:
    match strategy:
        case SolverStrategy.naive:
            return NaiveSolver()
        case SolverStrategy.nearest_neighbor:
            return NearestNeighborSolver()
        case SolverStrategy.two_opt:
            return Simple2PointSolver(max_iterations=settings.two_opt_max_iterations)


def _enforce_max_nodes(node_count: int, settings: Settings) -> None:
    if node_count <= settings.max_nodes:
        return
    raise HTTPException(
        status_code=422,
        detail=f"Too many nodes: {node_count} (max {settings.max_nodes})",
    )


@router.post("/solve", response_model=CoolTspSolution)
async def solve(
    request: SolveRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> CoolTspSolution:
    """Solve CoolTsp (start, deliveries, pickups, capacity); return solution."""
    node_count = 1 + len(request.deliveries) + len(request.pickups)
    _enforce_max_nodes(node_count, settings)

    strategy = _select_strategy(request.solver, settings)
    tsp_solver = _build_solver(strategy, settings)

    problem = CoolTspProblem(
        start=request.start,
        deliveries=request.deliveries,
        pickups=request.pickups,
        vehicle_capacity=request.vehicle_capacity,
    )
    cool_solver = CoolSolver(tsp_solver)
    result: CoolTspSolution = await asyncio.to_thread(cool_solver.solve, problem)

    log.info(
        "tsp_solved",
        endpoint="/v1/solve",
        node_count=node_count,
        deliveries=len(request.deliveries),
        pickups=len(request.pickups),
        solver=strategy.value,
        distance=result.solution.distance,
        pickup_detour_delta=result.pickup_detour_delta,
    )

    return result
