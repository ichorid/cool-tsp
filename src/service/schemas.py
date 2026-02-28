"""Pydantic schemas for API request/response."""

from enum import StrEnum

from pydantic import BaseModel, Field

from mytsp.models import Node, NodeType


class SolverStrategy(StrEnum):
    naive = "naive"
    nearest_neighbor = "nearest_neighbor"
    two_opt = "2opt"


def _default_start() -> Node:
    """Default depot/start node at (0, 0)."""
    return Node(x=0.0, y=0.0, name="depot", node_type=NodeType.START)


class SolveRequest(BaseModel):
    """Request body for POST /solve (CoolTsp: start, deliveries, pickups, capacity)."""

    start: Node = Field(
        default_factory=_default_start,
        description="Depot/start node (0,0 by default); always in the tour",
    )
    deliveries: list[Node] = Field(..., min_length=1, description="Delivery nodes")
    pickups: list[Node] = Field(default_factory=list, description="Pickup nodes")
    vehicle_capacity: float = Field(..., ge=0, description="Vehicle capacity")
    solver: SolverStrategy | None = Field(default=None, description="Solver strategy")
