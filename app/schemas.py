from pydantic import BaseModel, constr
from enum import Enum

class Division(str, Enum):
    Div1 = "Div 1"
    Div2 = "Div 2"

class UserBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1) # type: ignore
    codeforces_handle: constr(strip_whitespace=True, min_length=1, max_length=100) # type: ignore
    email: constr(strip_whitespace=True, min_length=1) # type: ignore
    division: Division
    rating: int


class UserCreate(UserBase):
    pass


class UserRead(BaseModel):
    id: int
    name: str
    codeforces_handle: str
    email: str
    division: Division
    status: str
    created_at: str
    role: str
    rating: int

    class Config:
        orm_mode = True