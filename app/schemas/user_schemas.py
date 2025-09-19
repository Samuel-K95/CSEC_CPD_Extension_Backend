from typing import List, Optional
from pydantic import BaseModel, constr, EmailStr
from enum import Enum
from datetime import datetime

from app.models import Division




class UserBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1) # type: ignore
    codeforces_handle: constr(strip_whitespace=True, min_length=1, max_length=100) # type: ignore
    email: EmailStr
    division: Division

class UserLogin(BaseModel):
    codeforces_handle: constr(strip_whitespace=True, min_length=1, max_length=100) # type: ignore
    password: constr(strip_whitespace=True, min_length=6) # type: ignore

class UserCreate(UserBase):
    password: str


class UserRead(BaseModel):
    id: int
    name: str
    codeforces_handle: str
    email: str
    division: Division
    status: str
    created_at: datetime
    role: str
    rating: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


class ChangeStatusRequest(BaseModel):
    status: str



class RatingHistoryEntry(BaseModel):
    contest_id: str
    old_rating: int
    new_rating: int
    timestamp: datetime

    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    codeforces_handle: Optional[str]
    division: Optional[str]
    current_rating: Optional[int]
    history: Optional[List[RatingHistoryEntry]] = None

    class Config:
        orm_mode = True