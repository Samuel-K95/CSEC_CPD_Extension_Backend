from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.schemas import contest_schemas
from typing import List, Optional
from datetime import datetime, timezone


async def log_rating_change(db: AsyncSession, user_id: int, contest_id: str, old_rating: int, new_rating: int):
    history_entry = models.RatingHistory(
        user_id=user_id,
        contest_id=contest_id,
        old_rating=old_rating,
        new_rating=new_rating
    )
    db.add(history_entry)
    await db.commit()
    await db.refresh(history_entry)
    

async def get_or_create_rating(db: AsyncSession, user_id: int) -> models.Rating:
    """
    Get the rating record for a user in a specific contest.
    If it doesn't exist, create a new one with default values.
    """
    result = await db.execute(
        select(models.Rating)
        .filter(models.Rating.user_id == user_id)
    )
    rating = result.scalars().first()

    if not rating:
        rating = models.Rating(
            user_id=user_id,
            current_rating=1400,
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(rating)
        await db.commit()
        await db.refresh(rating)

    return rating


async def update_rating(db: AsyncSession, user_id: int, new_rating: int) -> models.Rating:
    """
    Update the rating of a user.
    """
    rating = await get_or_create_rating(db, user_id)
    rating.current_rating = new_rating
    rating.last_updated = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(rating)
    return rating


async def apply_absence_penality(db: AsyncSession, user_id: int, penality: int) -> models.Rating:
    """
    Apply absence penality to a user's rating.
    """
    rating = await get_or_create_rating(db, user_id)
    rating.current_rating = max(0, rating.current_rating - penality)
    rating.last_updated = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(rating)
    return rating


async def get_leaderboard(db: AsyncSession, division: Optional[models.Division] = None) -> List[tuple[models.User, models.Rating]]:
    """
    Get the leaderboard of users sorted by their ratings.
    Optionally filter by division.
    """
    query = (
        select(models.User, models.Rating)
        .join(models.Rating, models.User.id == models.Rating.user_id)
        .filter(models.User.status == models.UserStatus.Active)
    )

    if division:
        query = query.filter(models.User.division == division)

    result = await db.execute(query.order_by(models.Rating.current_rating.desc()))
    return result.all()