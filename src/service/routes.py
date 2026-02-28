"""API route handlers."""

from fastapi import APIRouter

from mytsp import NaiveSolver, Node, TSPInstance
from service.schemas import SolveRequest, SolveResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> SolveResponse:
    """Solve a TSP instance and return the solution."""
    instance = TSPInstance(nodes=[Node(x=n.x, y=n.y, name=n.name) for n in request.nodes])
    solver = NaiveSolver()
    solution = solver.solve(instance)
    return SolveResponse(route=solution.route, distance=solution.distance)
