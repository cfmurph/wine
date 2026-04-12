from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.wine import PairingSearchResponse
from app.services.pairing_service import get_pairings_for_food

router = APIRouter(prefix="/pairings", tags=["pairings"])


@router.get("", response_model=PairingSearchResponse)
async def pairings(
    food: str = Query(..., description="Food or dish name, e.g. 'steak'"),
    db: AsyncSession = Depends(get_db),
):
    return await get_pairings_for_food(db, food)
