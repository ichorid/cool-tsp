"""Pydantic schemas for API request/response."""

from pydantic import BaseModel, Field


class NodeSchema(BaseModel):
    """Node in request/response."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    name: str | None = Field(default=None, description="Optional node label")


class SolveRequest(BaseModel):
    """Request body for POST /solve."""

    nodes: list[NodeSchema] = Field(..., min_length=2, description="Nodes to visit")


class SolveResponse(BaseModel):
    """Response body for POST /solve."""

    route: list[int] = Field(..., description="Indices of nodes in visit order")
    distance: float = Field(..., ge=0, description="Total tour distance")
