import math
from sqlalchemy.orm import Session
from app import models
from app.crud import ratings
from app.crud.ratings import log_rating_change

from app.services.codeforces import get_codeforces_standings_handles

def process_ratings_after_attendance(db: Session, contest_id: str, absence_penalty: int):
    """
    Process ratings for all users after attendance submission.
    Returns a summary of what happened (counts and rating changes).
    """
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise ValueError(f"Contest {contest_id} not found")

    # Fetch standings from Codeforces API
    standings = get_codeforces_standings_handles(contest.id)
    if not standings:
        # Handle case where standings are not available
        return {"error": "Could not fetch contest standings."}

    attendance_records = contest.attendance_records
    present_count = absent_count = permission_count = 0
    rating_changes = []

    for record in attendance_records:
        user = db.query(models.User).filter(models.User.id == record.user_id).first()
        if not user or user.status != models.UserStatus.ACTIVE:
            continue

        rating = ratings.get_or_create_rating(db, record.user_id)
        old_rating = rating.current_rating

        if record.status == models.AttendanceStatus.PRESENT:
            present_count += 1
            user_rank = standings.get(user.codeforces_handle)
            if user_rank is not None:
                new_rating = calculate_codeforces_rating(db, record.user_id, contest_id, standings)
                ratings.update_rating(db, record.user_id, new_rating)
                rating_changes.append({
                    "user_id": user.id,
                    "handle": user.codeforces_handle,
                    "old_rating": old_rating,
                    "new_rating": new_rating
                })
                log_rating_change(db, user_id=record.user_id, contest_id=contest_id, old_rating=old_rating, new_rating=new_rating)
    
        elif record.status == models.AttendanceStatus.ABSENT:
            absent_count += 1
            ratings.apply_absence_penalty(db, record.user_id, absence_penalty)
            new_rating = old_rating - absence_penalty
            rating_changes.append({
                "user_id": user.id,
                "handle": user.codeforces_handle,
                "old_rating": old_rating,
                "new_rating": new_rating
            })
            log_rating_change(db, user_id=record.user_id, contest_id=contest_id, old_rating=old_rating, new_rating=new_rating)

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


def calculate_codeforces_rating(db: Session, user_id: str, contest_id: str, standings: dict, k_factor: int = 40) -> int:
    """
    Calculate the new rating for a single participant using Elo-based logic.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user_rating = ratings.get_or_create_rating(db, user.id).current_rating
    user_rank = standings.get(user.codeforces_handle)

    if user_rank is None:
        # User did not participate, rating remains unchanged
        return user_rating

    expected_score_sum = 0.0
    actual_score_sum = 0.0
    
    # Get all users who participated in the contest
    present_users = db.query(models.User).filter(models.User.codeforces_handle.in_(standings.keys())).all()
    total_opponents = len(present_users) - 1

    for opponent in present_users:
        if opponent.id == user_id:
            continue

        opponent_rating = ratings.get_or_create_rating(db, opponent.id).current_rating
        opponent_rank = standings.get(opponent.codeforces_handle)

        # Expected score using Elo formula
        expected_score = 1 / (1 + math.pow(10, (opponent_rating - user_rating) / 400))
        expected_score_sum += expected_score

        # Actual score: 1 if user ranked better, 0 if worse, 0.5 if tie
        if user_rank < opponent_rank:
            actual_score_sum += 1
        elif user_rank == opponent_rank:
            actual_score_sum += 0.5

    expected_score_avg = expected_score_sum / total_opponents if total_opponents > 0 else 0
    actual_score_avg = actual_score_sum / total_opponents if total_opponents > 0 else 0

    # 3. Elo delta
    delta = k_factor * (actual_score_avg - expected_score_avg)

    # 4. Return new rating (rounded to int)
    return max(0, round(user_rating + delta))  # clamp to >= 0