from sqlalchemy.orm import Session
from app import models
from app.schemas import contest_schemas
from typing import List, Optional
from sqlalchemy import delete
import datetime


def create_contest(db: Session, contest_in: contest_schemas.ContestCreate) -> models.Contest:
    existing = db.query(models.Contest).filter(models.Contest.link == contest_in.link).first()
    if existing:
        raise ValueError(f"Contest with link '{contest_in.link}' already exists.")
    contest_date = datetime.datetime.utcnow()
    contest = models.Contest(
        name=contest_in.name,
        link=contest_in.link,
        division=contest_in.division,
        date=contest_date
    )
    db.add(contest)
    db.commit()
    db.refresh(contest)
    

    for user_id in contest_in.preparer_ids or []:
        db.execute(models.contest_preparer_table.insert().values(
            contest_id = contest.id,
            user_id = user_id,
            can_take_attendance = True
        ))

    db.commit()
    return contest

def get_contest(db: Session, contest_id: str) -> Optional[models.Contest]:
    return db.query(models.Contest).filter(models.Contest.id == contest_id).first()


def add_preparers_to_contest(db: Session, contest_id: str, preparer_ids: List[str]) -> models.Contest:
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError("Contest not found")

    existing_ids = {p.id for p in contest.preparers}

    for user_id in preparer_ids:
        if user_id not in existing_ids:
            db.execute(models.contest_preparer_table.insert().values(
                contest_id = contest.id,
                user_id = user_id,
                can_take_attendance = True
            ))

    db.commit()
    db.refresh(contest)
    return contest

def remove_preparers_from_contest(db: Session, contest_id: str, preparer_ids: List[str]) -> models.Contest:
    """
    Remove a preparer from a contest.
    """
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError("Contest not found")

    stmt = delete(models.contest_preparer_table).where(
        models.contest_preparer_table.c.contest_id == contest_id,
        models.contest_preparer_table.c.user_id.in_(preparer_ids)
    )
    db.execute(stmt)
    db.commit()
    db.refresh(contest)
    return contest

def get_user_contests(db: Session, user) -> list[models.Contest]:
    """
    Return all contests the user has participated in (attendance), or all contests if admin.
    """
    from app.models import UserRole, Contest, Attendance
    if user.role == UserRole.Admin:
        return db.query(Contest).all()
    else:
        return (
            db.query(Contest)
            .join(Attendance, Contest.id == Attendance.contest_id)
            .filter(Attendance.user_id == str(user.id))
            .all()
        )
    

def get_contests_by_division(db: Session, division: str) -> list[models.Contest]:
    """
    Return all contests for a given division (e.g., 'Div1' or 'Div2').
    """
    return db.query(models.Contest).filter(models.Contest.division == division).all()

def update_contest_preparers(db: Session, contest_id: str, preparers: List[str]) -> models.Contest:
    """
    Update the preparers for a specific contest.
    """
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError("Contest not found")

    # Remove all existing preparers
    stmt = delete(models.contest_preparer_table).where(
        models.contest_preparer_table.c.contest_id == contest_id
    )
    db.execute(stmt)

    # Add new preparers
    for user_id in preparers:
        db.execute(models.contest_preparer_table.insert().values(
            contest_id = contest.id,
            user_id = user_id,
            can_take_attendance = True
        ))

    db.commit()
    db.refresh(contest)
    return contest
