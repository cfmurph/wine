from typing import Optional, Literal
from pydantic import BaseModel


UserWineStatus = Literal["favorite", "tried", "want_to_try", "cellar"]


class UserWineCreate(BaseModel):
    wine_id: str
    status: UserWineStatus
    user_rating: Optional[float] = None
    notes: Optional[str] = None


class UserWineUpdate(BaseModel):
    status: Optional[UserWineStatus] = None
    user_rating: Optional[float] = None
    notes: Optional[str] = None


class UserWineOut(BaseModel):
    id: str
    wine_id: str
    status: str
    user_rating: Optional[float] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}
