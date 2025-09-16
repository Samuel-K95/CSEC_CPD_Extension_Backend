import enum
import datetime
import uuid
from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, Table, ForeignKey, Boolean
)

from sqlalchemy.orm import relationship
from typing import List, Optional
from .db import Base

# User

class Division(str, enum.Enum):
    Div1 = "Div 1"
    Div2 = "Div 2"  

class UserStatus(str, enum.Enum):
    Active = "Active"
    Terminated = "Terminated"
    NolongerActive = "No longer Active"


class UserRole(str, enum.Enum):
    Participant = "Participant"
    Admin = "Admin"

contest_preparer_table = Table(
    "contest_preparer_link",
    Base.metadata,
    Column("contest_id", String, ForeignKey("contests.id"), primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("can_take_attendance", Boolean, default=True)
)

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

    assigned_contests = relationship("Contest" ,secondary=contest_preparer_table, back_populates="preparers")
    ratings = relationship("Rating",back_populates="user")
    rating_history = relationship("RatingHistory", back_populates="user", cascade="all, delete-orphan")



class RatingHistory(Base):
    __tablename__ = "rating_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)

    old_rating = Column(Integer, nullable=False)
    new_rating = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="rating_history")
    contest = relationship("Contest", back_populates="rating_history")


# Contest + Link Model


class Contest(Base):
    __tablename__ = "contests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    link = Column(String, nullable=False)
    division = Column(Enum(Division), nullable=False)
    date = Column(DateTime, nullable=False)

    preparers = relationship("User", secondary=contest_preparer_table, back_populates="assigned_contests")
    attendance_records = relationship("Attendance", back_populates="contest")
    rating_history = relationship("RatingHistory", back_populates="contest", cascade="all, delete-orphan")



# Attendance

class AttendanceStatus(enum.Enum):
    PRESENT = "Present"
    PERMISSION = "Permission"
    ABSENT = "Absent"

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    contest_id = Column(String, ForeignKey("contests.id"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)

    contest = relationship("Contest", back_populates="attendance_records")


# Rating
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    current_rating = Column(Integer, default=1400, nullable=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="rating")
    