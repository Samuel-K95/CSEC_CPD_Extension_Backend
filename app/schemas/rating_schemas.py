from pydantic import BaseModel
from datetime import datetime


class RatingBase(BaseModel):
    current_rating: int

class RatingRead(RatingBase):
    id: str
    user_id: str
    last_updated: datetime

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    codeforces_handle: str
    division: str
    current_rating: int

    class Config:
        orm_mode = True


class RatingHistoryEntry(BaseModel):
    contest_id: int
    old_rating: int
    new_rating: int
    timestamp: datetime

    class Config:
        orm_mode = True