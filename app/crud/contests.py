from sqlalchemy.orm import Session
from app import models
from app.schemas import contest_schemas
from typing import List, Optional


def create_contest(db: Session, contest_in: contest_schemas.ContestCreate) -> models.Contest:
    contest = models.Contest(
        link=contest_in.link,
        division=contest_in.division
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