from sqlalchemy.orm import Session
from app import models
from typing import List
from app.services.codeforces import get_codeforces_standings_handles


def record_attendance(db: Session, contest_id: str, user_id: str, status: models.AttendanceStatus, commit=True):
    """
    Insert or update attendance record for a participant.
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

    if commit:
        db.commit()

    db.refresh(existing if existing else attendance)
    
    return existing if existing else attendance



def get_attendance_for_user(db:Session, user_id: str) -> List[models.Attendance]:
    """
    Get all attendance records for a specific user.
    """
    return (
        db.query(models.Attendance)
        .filter(models.Attendance.user_id == user_id)
        .all()
    )




def fetch_contest_attendance(db: Session, contest_id: str):
    """
    Returns a list of all active participants for the contest's division
    with their pre-marked attendance status present.
    """
    print("fetching contest attendance for contest:", contest_id)
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError("Contest not found")


    users = (
        db.query(models.User)
        .filter(
            models.User.status == models.UserStatus.Active,
            models.User.division == contest.division
        )
        .all()
    )

    competed_user_handles = get_codeforces_standings_handles(contest.link)
    print("competed user handles:", competed_user_handles)


    results = []
    for user in users:
        status = (
                models.AttendanceStatus.PRESENT
                if user.codeforces_handle in competed_user_handles
                else None
            )
        
        results.append(
            {
                "user_id": user.id,
                "username": user.name,
                "codeforces_handle": user.codeforces_handle,
                "division" : user.division,
                "status": status
            }
        )
    
    return results

