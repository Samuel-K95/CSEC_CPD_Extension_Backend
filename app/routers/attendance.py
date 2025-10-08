from fastapi import APIRouter, Depends, HTTPException
from app.crud.contests import get_contest
from app.dependencies.auth import get_current_user, require_admin, require_preparer
from sqlalchemy.orm import Session
from app.db import get_db
from app import models
from app.crud import attendance
from app.schemas import attendance_schemas as schemas
from app.crud.attendance import fetch_contest_attendance
from app.services.ratings import Codeforces


router = APIRouter(prefix="/api/attendance", tags=["attendance"])

# Dependency wrapper for preparer access
def preparer_dependency(contest_id: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return require_preparer(contest_id, current_user, db)

@router.post("/{contest_id}/attendance", response_model=dict)
def submit_attendance(
    contest_id: str,
    body: schemas.SubmitAttendanceRequest,
    db: Session = Depends(get_db),
    current_user = Depends(preparer_dependency)
):
    contest = get_contest(db=db, contest_id=contest_id)
    for record in body.attendance:
        attendance.record_attendance(db, contest_id, record.user_id, record.status, commit=False)

    db.commit()
    print("attendance recorded", body.attendance)
    print("ranking data received", body.ranking_data)

    # Save contest data snapshot for rollback/replay
    attendance.save_contest_data_snapshot(db, contest_id, body.attendance, body.ranking_data)

    rating_summary = []
    codeforces = Codeforces(db=db, div=contest.division, ranking=body.ranking_data, attendance=body.attendance)
    rating_updates = codeforces.calculate_final_ratings(penality=50) # Penality not set yet!
    print("rating updates calculated", rating_updates)
    
    # Apply rating updates in all tables related to user ratings
    for user_id, delta in rating_updates.items():
        updated_user = attendance.apply_rating_update(db, user_id, delta, commit=False) 
        if updated_user:
            rating_summary.append({
                "user_id": user_id,
                "contest_id": contest_id,
                "old_rating": updated_user.rating - delta,
                "new_rating": updated_user.rating,
                "delta": delta
            })
    
    # Batch insert RatingHistory records using CRUD function
    attendance.record_rating_history_batch(db, rating_summary)

    db.commit()

    return {
        "message": "Attendance and ranking data recorded",
        "ranking_data": body.ranking_data,
        "rating_summary": rating_summary
    }


@router.get("/{contest_id}/attendance", response_model=dict)
def get_contest_attendance( 
    contest_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(preparer_dependency)
):
    """
    Preparer-only: Get list of all active participants in this contest's division.
    Pre-mark those who actually competed as Present.
    """
    print("getting attendance for contest", contest_id)
    try:
        # check for the contest id inside the attendance table
        data = attendance.fetch_contest_attendance(db, contest_id)
    except ValueError as e:
        print("error", e)
        raise HTTPException(status_code=404, detail=str(e))

    return {"contest_id": contest_id, "participants_info": data}



@router.put("/{contest_id}/attendance", response_model=dict)
def update_attendance(
    contest_id: str,
    body: schemas.UpdateAttendanceRequest,
    db: Session = Depends(get_db),
    current_user = Depends(preparer_dependency)
):
    """
    Update attendance records for a specific contest.
    """
    # 1. Rollback all previous rating and attendance effects for this contest
    attendance.rollback_contest_ratings_and_attendance(db, contest_id)

    # 2. Update attendance records (fresh)
    for record in body.attendance:
        attendance.record_attendance(db, contest_id, record.user_id, record.status, commit=False)

    db.commit()
    print("attendance updated", body.attendance)
    print("ranking data received", body.ranking_data)

    # Save contest data snapshot for rollback/replay
    attendance.save_contest_data_snapshot(db, contest_id, body.attendance, body.ranking_data)

    # 3. Get contest info for division
    contest = get_contest(db=db, contest_id=contest_id)

    rating_summary = []
    codeforces = Codeforces(db=db, div=contest.division, ranking=body.ranking_data, attendance=body.attendance)
    rating_updates = codeforces.calculate_final_ratings(penality=50) # Penality not set yet!
    print("rating updates calculated", rating_updates)

    # 4. Apply rating updates in all tables related to user ratings
    for user_id, delta in rating_updates.items():
        updated_user = attendance.apply_rating_update(db, user_id, delta, commit=False)
        if updated_user:
            rating_summary.append({
                "user_id": user_id,
                "contest_id": contest_id,
                "old_rating": updated_user.rating - delta,
                "new_rating": updated_user.rating,
                "delta": delta
            })

    # 5. Batch insert RatingHistory records using CRUD function
    attendance.record_rating_history_batch(db, rating_summary)

    db.commit()

    # 6. Replay all subsequent contests for true rating accuracy
    print(f"[REPLAY] Replaying all subsequent contests after {contest_id}...")
    attendance.replay_subsequent_contests(db, contest_id)
    print(f"[REPLAY] Replay complete for all subsequent contests after {contest_id}.")

    return {
        "message": "Attendance and ratings updated (with rollback and replay)",
        "attendance": body.attendance,
        "ranking_data": body.ranking_data,
        "rating_summary": rating_summary
    }