"""Data models for TSP instances and solutions."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(StrEnum):
    """Type of node in a CoolTsp route or problem."""

    NONE = "none"
    START = "start"
    DELIVERY = "delivery"
    PICKUP = "pickup"


class Node(BaseModel):
    """Node with 2D coordinates, optional name and demand (e.g. package size)."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    name: str | None = Field(default=None, description="Optional node label")
    demand: float = Field(default=0, ge=0, description="Demand (e.g. package size)")
    node_type: NodeType | None = Field(default=None, description="Node role")


class TSPInstance(BaseModel):
    """A TSP problem instance: a list of nodes to visit."""

    nodes: list[Node] = Field(..., min_length=2, description="Nodes to visit")


class TSPSolution(BaseModel):
    """A TSP solution: ordered route and total distance."""

    route: list[int] = Field(..., description="Indices of nodes in visit order")
    distance: float = Field(..., ge=0, description="Total tour distance")
    stats: dict[str, Any] | None = Field(
        default=None, description="Optional solver statistics (e.g. 2-opt iterations)"
    )


def _default_start() -> Node:
    """Default depot/start node at (0, 0)."""
    return Node(x=0.0, y=0.0, name="depot", node_type=NodeType.START)


class CoolTspProblem(BaseModel):
    """CoolTsp problem: start (depot), deliveries, pickups, and vehicle capacity."""

    start: Node = Field(
        default_factory=_default_start,
        description="Depot/start node (0,0 by default); always in the tour",
    )
    deliveries: list[Node] = Field(..., min_length=1, description="Delivery TSP nodes")
    pickups: list[Node] = Field(default_factory=list, description="Pickup TSP nodes")
    vehicle_capacity: float = Field(..., ge=0, description="Vehicle capacity")


class CoolTspSolution(BaseModel):
    """CoolSolver result: TSP tour (optionally one pickup) and unused pickups."""

    solution: TSPSolution = Field(
        ..., description="Route and distance (delivery tour, or with one pickup detour)"
    )
    nodes: list[Node] = Field(
        ...,
        description="Tour nodes in route order (depot, deliveries, possibly one pickup)",
    )
    unused_nodes: list[Node] = Field(
        default_factory=list,
        description="Pickup nodes not visited (unused), with node_type set",
    )
    pickup_detour_delta: float = Field(
        default=0.0,
        ge=0,
        description="Extra distance from the inserted pickup detour, or 0 if none",
    )
