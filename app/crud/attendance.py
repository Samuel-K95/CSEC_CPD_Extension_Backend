from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app import models
from typing import List
from app.services.codeforces import get_codeforces_standings_handles
from app.schemas import  user_schemas
from app.models import ContestDataSnapshot
import datetime, asyncio
import enum
from app.crud.contests import get_contest
from app.services.ratings import Codeforces
from app.models import AttendanceStatus
from app.models import ContestDataSnapshot
from app.models import Contest, AttendanceStatus

def to_serializable(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if hasattr(obj, "dict"):
        return {k: to_serializable(v) for k, v in obj.dict().items()}
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(i) for i in obj]
    return obj

async def record_attendance(db: AsyncSession, contest_id: str, user_id: str, status: models.AttendanceStatus, commit=True):
    """
    Insert or update attendance record for a participant.
    """
    result = await db.execute(
        select(models.Attendance).filter(
            models.Attendance.contest_id == contest_id, models.Attendance.user_id == user_id
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.status = status
        obj = existing
    else:
        attendance = models.Attendance(
            contest_id=contest_id,
            user_id=user_id,
            status=status
        )
        db.add(attendance)
        await db.flush()
        obj = attendance

    if commit:
        await db.commit()

    await db.refresh(obj)
    return obj



async def get_attendance_for_user(db: AsyncSession, user_id: str) -> List[models.Attendance]:
    """
    Get all attendance records for a specific user.
    """
    result = await db.execute(
        select(models.Attendance).filter(models.Attendance.user_id == user_id)
    )
    return result.scalars().all()



async def fetch_contest_attendance(db: AsyncSession, contest_id: str):
    """
    Returns a list of all attendance records for a specific contest_id,
    including user info and attendance status.
    """
    print("fetching contest attendance for contest:", contest_id)
    result = await db.execute(
        select(models.Attendance, models.User)
        .join(models.User, models.Attendance.user_id == models.User.id)
        .filter(models.Attendance.contest_id == contest_id)
    )
    records = result.all()
    results = []
    for attendance, user in records:
        results.append({
            "user_id": user.id,
            "username": user.name,
            "codeforces_handle": user.codeforces_handle,
            "division": user.division,
            "status": attendance.status.value
        })
    return results

async def apply_rating_update(db: AsyncSession, user_id: str, delta: int, commit=True):
    """
    Update the user's rating by adding delta. Returns the updated user object.
    """
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None


    user.rating = (user.rating or 0) + delta
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def record_rating_history_batch(db: AsyncSession, rating_summary: list):
    """
    Batch insert RatingHistory records from a list of rating summary dicts.
    Each dict should have keys: user_id, contest_id, old_rating, new_rating.
    """
    for entry in rating_summary:
        history_record = models.RatingHistory(
            user_id=entry['user_id'],
            contest_id=entry['contest_id'],
            old_rating=entry['old_rating'],
            new_rating=entry['new_rating']
        )
        db.add(history_record)

    await db.commit()

async def rollback_contest_ratings_and_attendance(db: AsyncSession, contest_id: str):
    """
    Revert all users' ratings and attendance for a contest to the state before the contest.
    - Sets user.rating to old_rating from RatingHistory for this contest
    - Deletes all RatingHistory entries for this contest
    - Deletes all Attendance records for this contest
    """
    print(f"[ROLLBACK] Starting rollback for contest_id={contest_id}")
    # 1. Revert user ratings
    histories_result = await db.execute(select(models.RatingHistory).filter(models.RatingHistory.contest_id == contest_id))
    histories = histories_result.scalars().all()
    for history in histories:
        user_result = await db.execute(select(models.User).filter(models.User.id == history.user_id))
        user = user_result.scalars().first()
        if user:
            print(f"[ROLLBACK] Reverting user_id={user.id} rating from {user.rating} to {history.old_rating}")
            user.rating = history.old_rating
            db.add(user)
    # 2. Delete RatingHistory entries
    await db.execute(delete(models.RatingHistory).filter(models.RatingHistory.contest_id == contest_id))
    print(f"[ROLLBACK] Deleted RatingHistory entries for contest_id={contest_id}")
    # 3. Delete Attendance records
    await db.execute(delete(models.Attendance).filter(models.Attendance.contest_id == contest_id))
    print(f"[ROLLBACK] Deleted Attendance records for contest_id={contest_id}")
    await db.commit()
    print(f"[ROLLBACK] Rollback complete for contest_id={contest_id}")

async def save_contest_data_snapshot(db: AsyncSession, contest_id: str, attendance: list, ranking_data: list):
    """
    Save or update the contest data snapshot for a contest.
    """
    attendance_serializable = [to_serializable(a) for a in attendance]
    ranking_data_serializable = [to_serializable(r) for r in ranking_data]

    result = await db.execute(select(ContestDataSnapshot).filter(ContestDataSnapshot.contest_id == contest_id))
    existing = result.scalars().first()
    if existing:
        print(f"[SNAPSHOT] Updating existing snapshot for contest_id={contest_id}")
        existing.attendance_snapshot = attendance_serializable
        existing.ranking_data_snapshot = ranking_data_serializable
        existing.created_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    else:
        print(f"[SNAPSHOT] Creating new snapshot for contest_id={contest_id}")
        snapshot = ContestDataSnapshot(
            contest_id=contest_id,
            attendance_snapshot=attendance_serializable,
            ranking_data_snapshot=ranking_data_serializable
        )
        db.add(snapshot)
    await db.commit()

async def fetch_contest_data_snapshot(db: AsyncSession, contest_id: str):
    """
    Fetch the contest data snapshot for a contest.
    Returns (attendance, ranking_data) or (None, None) if not found.
    """
    result = await db.execute(select(ContestDataSnapshot).filter(ContestDataSnapshot.contest_id == contest_id))
    snap = result.scalars().first()
    if snap:
        print(f"[SNAPSHOT] Fetched snapshot for contest_id={contest_id}")
        return snap.attendance_snapshot, snap.ranking_data_snapshot
    print(f"[SNAPSHOT] No snapshot found for contest_id={contest_id}")
    return None, None


async def get_subsequent_contests(db: AsyncSession, contest_id: str):
    """
    Return all contests in the same division with date > given contest, ordered by date.
    """
    base_contest_result = await db.execute(select(Contest).filter(Contest.id == contest_id))
    base_contest = base_contest_result.scalars().first()
    if not base_contest:
        print(f"[REPLAY] Contest {contest_id} not found.")
        return []
    contests_result = await db.execute(
        select(Contest)
        .filter(
            Contest.division == base_contest.division,
            Contest.date > base_contest.date
        )
        .order_by(Contest.date.asc())
    )
    contests = contests_result.scalars().all()
    print(f"[REPLAY] Found {len(contests)} subsequent contests after {contest_id}.")
    return contests

async def replay_contest(db: AsyncSession, contest_id: str):
    """
    Rollback and reapply a single contest using its stored snapshot.
    """
    print(f"[REPLAY] Replaying contest {contest_id}")
    await rollback_contest_ratings_and_attendance(db, contest_id)
    attendance, ranking_data = await fetch_contest_data_snapshot(db, contest_id)
    if attendance is None or ranking_data is None:
        print(f"[REPLAY] No snapshot for contest {contest_id}, skipping replay.")
        return

    contest = await get_contest(db=db, contest_id=contest_id)
    # Re-apply attendance
    for record in attendance:
        # Convert string status from snapshot back to Enum member
        status_enum = AttendanceStatus(record['status'])
        await record_attendance(db, contest_id, record['user_id'], status_enum, commit=False)
    await db.commit()
    # Re-apply ratings
    codeforces = Codeforces(db=db, div=contest.division, ranking=ranking_data, attendance=attendance)
    rating_updates = await codeforces.calculate_final_ratings(penality=50)
    rating_summary = []
    for user_id, delta in rating_updates.items():
        updated_user = await apply_rating_update(db, user_id, delta, commit=False)
        if updated_user:
            rating_summary.append({
                "user_id": user_id,
                "contest_id": contest_id,
                "old_rating": updated_user.rating - delta,
                "new_rating": updated_user.rating,
                "delta": delta
            })
    await record_rating_history_batch(db, rating_summary)
    await db.commit()
    print(f"[REPLAY] Finished replay for contest {contest_id}")

async def replay_subsequent_contests(db: AsyncSession, contest_id: str):
    """
    Rollback and replay all subsequent contests after the given contest.
    """
    contests = await get_subsequent_contests(db, contest_id)
    for contest in contests:
        await replay_contest(db, contest.id)