import math
from sqlalchemy.orm import Session
from app import models, crud
from app.crud.ratings import log_rating_change

def process_ratings_after_attendance(db: Session, contest_id: str, absence_penalty: int):
    """
    Process ratings for all users after attendance submission.
    Returns a summary of what happened (counts and rating changes).
    """
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError(f"Contest {contest_id} not found")

    attendance_records = contest.attendance_records
    present_count = absent_count = permission_count = 0
    rating_changes = []

    for record in attendance_records:
        user = db.query(models.User).filter(models.User.id == record.user_id).first()
        if not user or user.status != models.UserStatus.ACTIVE:
            continue

        rating = crud.ratings.get_or_create_rating(db, record.user_id)
        old_rating = rating.current_rating

        if record.status == models.AttendanceStatus.PRESENT:
            present_count += 1
            new_rating = calculate_codeforces_rating(db, record.user_id, contest_id)
            crud.ratings.update_rating(db, record.user_id, new_rating)
            rating_changes.append({
                "user_id": user.id,
                "handle": user.codeforces_handle,
                "old_rating": old_rating,
                "new_rating": new_rating
            })
            log_rating_change(db, user_id=record.user_id, contest_id=contest_id, old_rating=old_rating, new_rating=new_rating)
    
            

        elif record.status == models.AttendanceStatus.ABSENT:
            absent_count += 1
            crud.ratings.apply_absence_penalty(db, record.user_id, absence_penalty)
            rating_changes.append({
                "user_id": user.id,
                "handle": user.codeforces_handle,
                "old_rating": old_rating,
                "new_rating": old_rating + absence_penalty
            })

            log_rating_change(db, user_id=record.user_id, contest_id=contest_id, old_rating=old_rating, new_rating=old_rating + absence_penalty)

        elif record.status == models.AttendanceStatus.PERMISSION:
            permission_count += 1

            log_rating_change(db, user_id=record.user_id, contest_id=contest_id, old_rating=old_rating, new_rating=old_rating)


    db.commit()

    return {
        "present": present_count,
        "absent": absent_count,
        "permission": permission_count,
        "rating_changes": rating_changes
    }


def calculate_codeforces_rating(db: Session, user_id: str, contest_id: str, k_factor: int = 40) -> int:
    """
    Calculate the new rating for a single participant using Elo-based logic.
    Must be called after all attendance is saved.
    """

    # 1. Get all participants who were present in this contest
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    present_records = [r for r in contest.attendance_records if r.status == models.AttendanceStatus.PRESENT]

    # Get the current user's record + rating
    user_record = next((r for r in present_records if r.user_id == user_id), None)
    if not user_record:
        raise ValueError(f"User {user_id} did not participate in this contest")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    user_rating = crud.ratings.get_or_create_rating(db, user.id).current_rating

    # Sort participants by contest performance (rank must come from standings)
    # For now, assume user_record has rank attribute (1 = best)
    present_records.sort(key=lambda r: r.rank)

    # 2. Compute expected and actual scores
    expected_score_sum = 0.0
    actual_score_sum = 0.0
    total_opponents = len(present_records) - 1

    for opponent_record in present_records:
        if opponent_record.user_id == user_id:
            continue

        opponent_rating = crud.ratings.get_or_create_rating(db, opponent_record.user_id).current_rating

        # Expected score using Elo formula
        expected_score = 1 / (1 + math.pow(10, (opponent_rating - user_rating) / 400))
        expected_score_sum += expected_score

        # Actual score: 1 if user ranked better, 0 if worse, 0.5 if tie
        if user_record.rank < opponent_record.rank:
            actual_score_sum += 1
        elif user_record.rank == opponent_record.rank:
            actual_score_sum += 0.5
        # else 0 if user ranked worse

    expected_score_avg = expected_score_sum / total_opponents if total_opponents > 0 else 0
    actual_score_avg = actual_score_sum / total_opponents if total_opponents > 0 else 0

    # 3. Elo delta
    delta = k_factor * (actual_score_avg - expected_score_avg)

    # 4. Return new rating (rounded to int)
    return max(0, round(user_rating + delta))  # clamp to >= 0