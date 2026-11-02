from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.winery import MarketResponse
from app.services.winery_service import get_market

router = APIRouter(prefix="/market", tags=["market"])


@router.get("", response_model=MarketResponse)
async def market(db: AsyncSession = Depends(get_db)):
    return await get_market(db)
