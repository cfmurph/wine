"""User accounts and saved wines."""

from sqlalchemy import (
    Column, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.base import _uuid


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String(256), unique=True, index=True, nullable=False)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_wines = relationship("UserWine", back_populates="user", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="user", cascade="all, delete-orphan")


class UserWine(Base):
    __tablename__ = "user_wine"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        SAEnum("favorite", "tried", "want_to_try", "cellar", name="user_wine_status"),
        nullable=False,
    )
    user_rating = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "wine_id", name="uq_user_wine"),)

    user = relationship("User", back_populates="user_wines")
    wine = relationship("Wine", back_populates="user_wines")
