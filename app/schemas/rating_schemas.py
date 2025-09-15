from pydantic import BaseModel
from datetime import datetime


class RatingBase(BaseModel):
    current_rating: int

class RatingRead(RatingBase):
    id: str
    user_id: str
    last_updated: datetime