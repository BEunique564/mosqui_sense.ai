"""Spray operations and OR-Tools optimization — Module 9."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class VehicleSpec(BaseModel):
    id: str
    capacity_liters: float
    fuel_tank: float


class OptimizeSprayRequest(BaseModel):
    ward_ids: list[UUID]
    vehicles: list[VehicleSpec]
    workers_available: int = Field(ge=1)
    depot_location: tuple[float, float]
    max_route_hours: float = 8.0


class OptimizeSprayResponse(BaseModel):
    routes: list[dict]
    total_fuel_liters: float
    estimated_cost_inr: float
    solver_status: str


@router.post("/optimize", response_model=OptimizeSprayResponse)
async def optimize_spray_routes(request: OptimizeSprayRequest):
    """Generate optimal fogging routes using Google OR-Tools VRP."""
    from app.services.optimization.vrp_solver import solve_spray_vrp

    result = solve_spray_vrp(request)
    return result
