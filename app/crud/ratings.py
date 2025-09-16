from sqlalchemy.orm import Session
from app import models
from app.schemas import contest_schemas
from typing import List, Optional
from datetime import datetime

def get_or_create_rating(db: Session, user_id: int) -> models.Rating:
    """
    Get the rating record for a user in a specific contest.
    If it doesn't exist, create a new one with default values.
    """
    rating = (
        db.query(models.Rating)
        .filter(models.Rating.user_id == user_id)
        .first()
    )

    if not rating:
        rating = models.Rating(
            user_id=user_id,
            current_rating=1400,
            last_updated=datetime.utcnow()
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)

    return rating


def update_rating(db: Session, user_id: int, new_rating: int) -> models.Rating:
    """
    Update the rating of a user.
    """
    rating = get_or_create_rating(db, user_id)
    rating.current_rating = new_rating
    rating.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(rating)
    return rating


def apply_absence_penality(db: Session, user_id: int, penality: int) -> models.Rating:
    """
    Apply absence penality to a user's rating.
    """
    rating = get_or_create_rating(db, user_id)
    rating.current_rating = max(0, rating.current_rating - penality)
    rating.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(rating)
    return rating


def get_leaderboard(db: Session, division: Optional[models.Division] = None) -> List[models.Rating]:
    """
    Get the leaderboard of users sorted by their ratings.
    Optionally filter by division.
    """
    query = (
        db.query(models.User, models.Rating)
        .join(models.Rating, models.User.id == models.Rating.user_id)
        .filter(models.User.status == models.UserStatus.Active)
    )

    if division:
        query = query.filter(models.User.division == division)

    return query.order_by(models.Rating.current_rating.desc()).all()