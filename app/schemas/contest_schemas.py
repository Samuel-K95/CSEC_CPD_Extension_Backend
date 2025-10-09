from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.user_schemas import UserRead
from app.models import Division

class ContestBase(BaseModel):
    link: str
    name: str
    division: Division

class ContestCreate(ContestBase):
    preparer_ids: Optional[List[str]] = []

class ContestUpdatePreparers(BaseModel):
    preparers: List[str]

class ContestRead(ContestBase):
    id: str
    date: datetime
    preparers: List[UserRead] = []
    class Config:
        orm_mode = True

class ContestPreparers(UserRead):
    preparers: List[UserRead] = []
    class Config:
        orm_mode = True

class AssignPreparersRequest(BaseModel):
    preparer_ids: List[str]
