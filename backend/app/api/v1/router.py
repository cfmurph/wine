from fastapi import APIRouter

from app.api.v1.endpoints import wines, pairings, cellar, auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(wines.router)
api_router.include_router(pairings.router)
api_router.include_router(cellar.router)
