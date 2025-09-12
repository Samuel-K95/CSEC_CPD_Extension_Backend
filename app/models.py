import enum
import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from .db import Base

class Division(str, enum.Enum):
    Div1 = "Div 1"
    Div2 = "Div 2"  

class UserStatus(str, enum.Enum):
    Active = "Active"
    Terminated = "Terminated"
    NolongerActive = "No longer Active"


class UserRole(str, enum.Enum):
    Participant = "Participant"
    ContestPreparer = "Contest Preparer"
    Admin = "Admin"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    codeforces_handle = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    division = Column(Enum(Division), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.Active, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    role = Column(Enum(UserRole), default=UserRole.Participant, nullable=False)
    rating = Column(Integer, default=1400, nullable=False)