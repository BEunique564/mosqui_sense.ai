"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import predictions, citizen, spray

api_router = APIRouter()
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(citizen.router, prefix="/citizen", tags=["citizen"])
api_router.include_router(spray.router, prefix="/spray", tags=["spray"])
