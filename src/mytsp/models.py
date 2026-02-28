"""Data models for TSP instances and solutions."""

from pydantic import BaseModel, Field


class Node(BaseModel):
    """A node with 2D coordinates and optional name."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    name: str | None = Field(default=None, description="Optional node label")


class TSPInstance(BaseModel):
    """A TSP problem instance: a list of nodes to visit."""

    nodes: list[Node] = Field(..., min_length=2, description="Nodes to visit")


class TSPSolution(BaseModel):
    """A TSP solution: ordered route and total distance."""

    route: list[int] = Field(..., description="Indices of nodes in visit order")
    distance: float = Field(..., ge=0, description="Total tour distance")
