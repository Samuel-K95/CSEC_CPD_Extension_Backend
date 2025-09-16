from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user, require_admin, require_preparer
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.crud import attendance
from app.schemas import attendance_schemas as schemas
from app.crud.attendance import fetch_contest_attendance
from app.services.ratings import process_ratings_after_attendance


router = APIRouter(prefix="/api/attendance", tags=["attendance"])

def preparer_dependency(contest_id: str):
    return require_preparer(contest_id)

@router.post("/contests/{contest_id}/attendance")
def submit_attendance(
    contest_id: str,
    data: list[schemas.AttendanceCreate],
    db: Session = Depends(get_db),
    current_user = Depends(preparer_dependency)
):
    for record in data:
        attendance.record_attendance(db, contest_id, record.user_id, record.status, commit=False)

    db.commit()

    
    # Trigger rating update
    process_ratings_after_attendance(db, contest_id, absence_penalty=-50)

    return {"message": "Attendance recorded and ratings updated"}



@router.get("/{contest_id}/attendance")
def get_contest_attendance( 
    contest_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(preparer_dependency)
):
    """
    Preparer-only: Get list of all active participants in this contest's division.
    Pre-mark those who actually competed as Present.
    """
    try:
        data = fetch_contest_attendance(db, contest_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"contest_id": contest_id, "participants": data}