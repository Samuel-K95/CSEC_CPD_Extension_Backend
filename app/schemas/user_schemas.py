from typing import List, Optional
from pydantic import BaseModel, constr, EmailStr
from enum import Enum
from datetime import datetime

from app.models import Division



class UserUpdate(BaseModel):
    name: str
    email: str
    codeforces_handle: Optional[str] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None



class UserBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1) # type: ignore
    codeforces_handle: constr(strip_whitespace=True, min_length=1, max_length=100) # type: ignore
    email: EmailStr
    division: Division

class UserLogin(BaseModel):
    id: int
    codeforces_handle: constr(strip_whitespace=True, min_length=1, max_length=100) # type: ignore
    role: str
    access_token: str
    refresh_token: str
    token_type: str
    division: Division
    name: str
    email: str
    current_rating: int
    

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
    response: Optional[str] = None  


    class Config:
        orm_mode = True

class Token(BaseModel):
    pass

class TokenData(BaseModel):
    username: str | None = None


class ChangeStatusRoleandDivision(BaseModel):
    status: str
    role: str
    division: Division




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
    current_rating: int
    role: str
    history: Optional[List[RatingHistoryEntry]] = None

    class Config:
        orm_mode = True