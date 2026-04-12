from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.wine import User
from app.schemas.cellar import UserWineCreate, UserWineUpdate, UserWineOut
from app.services.auth_service import get_current_user
from app.services.user_cellar_service import (
    list_cellar,
    add_to_cellar,
    update_cellar_entry,
    remove_from_cellar,
)

router = APIRouter(prefix="/users/me", tags=["cellar"])


@router.get("/cellar", response_model=list[UserWineOut])
async def get_cellar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_cellar(db, current_user.id)


@router.post("/cellar", response_model=UserWineOut)
async def add_wine(
    payload: UserWineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_to_cellar(db, current_user.id, payload)


@router.patch("/cellar/{wine_id}", response_model=UserWineOut)
async def update_wine(
    wine_id: str,
    payload: UserWineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await update_cellar_entry(db, current_user.id, wine_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Wine not in cellar")
    return result


@router.delete("/cellar/{wine_id}", status_code=204)
async def remove_wine(
    wine_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await remove_from_cellar(db, current_user.id, wine_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Wine not in cellar")
