from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.winery import WineryCompareRequest, WineryCompareResponse, WineryDetail, WineryListResponse
from app.services.winery_service import get_wineries, list_wineries

router = APIRouter(prefix="/wineries", tags=["wineries"])


def _weights(
    brand: float = Query(1.0, ge=0),
    land: float = Query(1.0, ge=0),
    tourism: float = Query(1.0, ge=0),
    operations: float = Query(1.0, ge=0),
) -> dict[str, float]:
    return {"brand": brand, "land": land, "tourism": tourism, "operations": operations}


@router.get("", response_model=WineryListResponse)
async def search(
    q: str | None = Query(None, description="Winery name or city"),
    region: str | None = Query(None),
    for_sale: bool = Query(False),
    min_asking: float | None = Query(None, ge=0),
    max_asking: float | None = Query(None, ge=0),
    min_cases: int | None = Query(None, ge=0),
    weights: dict[str, float] = Depends(_weights),
    db: AsyncSession = Depends(get_db),
):
    return await list_wineries(db, weights, q, region, for_sale, min_asking, max_asking, min_cases)


@router.post("/compare", response_model=WineryCompareResponse)
async def compare(payload: WineryCompareRequest, db: AsyncSession = Depends(get_db)):
    weights = {
        "brand": payload.brand, "land": payload.land,
        "tourism": payload.tourism, "operations": payload.operations,
    }
    return WineryCompareResponse(wineries=await get_wineries(db, payload.winery_ids, weights))


@router.get("/{winery_id}", response_model=WineryDetail)
async def get_winery(
    winery_id: str,
    weights: dict[str, float] = Depends(_weights),
    db: AsyncSession = Depends(get_db),
):
    results = await get_wineries(db, [winery_id], weights)
    if not results:
        raise HTTPException(status_code=404, detail="Winery not found")
    return results[0]
