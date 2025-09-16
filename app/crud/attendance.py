from sqlalchemy.orm import Session
from app import models
from app.schemas import contest_schemas
from typing import List, Optional
import uuid

def record_attendance(db: Session, contest_id:str, user_id:int, status: models.AttendanceStatus) -> models.Attendance:
    """
    Insert or Update a participants attendance for a specific contest.
    """

    existing = (
        db.query(models.Attendance)
        .filter(models.Attendance.contest_id == contest_id, models.Attendance.user_id == user_id)
        .first()
    )

    if existing:
        existing.status = status
    else:
        attendance = models.Attendance(
            contest_id=contest_id,
            user_id=user_id,
            status=status
        )
        db.add(attendance)
        db.commit()

    db.refresh(existing if existing else attendance)

    return existing if existing else attendance

def get_attendance_for_contest(db:Session, contest_id:str) -> List[models.Attendance]:
    """
    Get all attendance records for a specific contest.
    """
    return (
        db.query(models.Attendance)
        .filter(models.Attendance.contest_id == contest_id)
        .all()
    )

def get_attendance_for_user(db:Session, user_id: str) -> List[models.Attendance]:
    """
    Get all attendance records for a specific user.
    """
    return (
        db.query(models.Attendance)
        .filter(models.Attendance.user_id == user_id)
        .all()
    )