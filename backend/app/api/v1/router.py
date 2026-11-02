from fastapi import APIRouter

from app.api.v1.endpoints import wines, pairings, cellar, auth, wineries, market, deals

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(wines.router)
api_router.include_router(pairings.router)
api_router.include_router(cellar.router)
api_router.include_router(wineries.router)
api_router.include_router(market.router)
api_router.include_router(deals.router)
