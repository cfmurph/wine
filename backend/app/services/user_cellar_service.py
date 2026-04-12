"""
User cellar service — manage saved wines, ratings, and tasting notes.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wine import UserWine
from app.schemas.cellar import UserWineCreate, UserWineUpdate, UserWineOut
from app.core.logging import logger


async def list_cellar(db: AsyncSession, user_id: str) -> list[UserWineOut]:
    stmt = select(UserWine).where(UserWine.user_id == user_id)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [UserWineOut.model_validate(r) for r in rows]


async def add_to_cellar(
    db: AsyncSession, user_id: str, payload: UserWineCreate
) -> UserWineOut:
    stmt = select(UserWine).where(
        UserWine.user_id == user_id,
        UserWine.wine_id == payload.wine_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.status = payload.status
        if payload.user_rating is not None:
            existing.user_rating = payload.user_rating
        if payload.notes is not None:
            existing.notes = payload.notes
        await db.flush()
        return UserWineOut.model_validate(existing)

    entry = UserWine(
        user_id=user_id,
        wine_id=payload.wine_id,
        status=payload.status,
        user_rating=payload.user_rating,
        notes=payload.notes,
    )
    db.add(entry)
    await db.flush()
    return UserWineOut.model_validate(entry)


async def update_cellar_entry(
    db: AsyncSession, user_id: str, wine_id: str, payload: UserWineUpdate
) -> UserWineOut | None:
    stmt = select(UserWine).where(
        UserWine.user_id == user_id,
        UserWine.wine_id == wine_id,
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        return None

    if payload.status is not None:
        entry.status = payload.status
    if payload.user_rating is not None:
        entry.user_rating = payload.user_rating
    if payload.notes is not None:
        entry.notes = payload.notes
    await db.flush()
    return UserWineOut.model_validate(entry)


async def remove_from_cellar(
    db: AsyncSession, user_id: str, wine_id: str
) -> bool:
    stmt = select(UserWine).where(
        UserWine.user_id == user_id,
        UserWine.wine_id == wine_id,
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if entry is None:
        return False
    await db.delete(entry)
    await db.flush()
    return True
