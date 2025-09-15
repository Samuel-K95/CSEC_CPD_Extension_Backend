from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.user_schemas import UserRead

class ContestBase(BaseModel):
    link: str
    division: str

class ContestCreate(ContestBase):
    preparer_ids: Optional[List[str]] = []

class ContestRead(ContestBase):
    id: str
    date: datetime
    preparers: List[UserRead] = []

