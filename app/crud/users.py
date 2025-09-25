from sqlalchemy.orm import Session
from ..models import User, UserStatus
from ..schemas.user_schemas import UserCreate
from ..security import hash_password
from app import models


def get_user_by_handle(db: Session, handle: str):
    return db.query(User).filter(User.codeforces_handle == handle).first()

def create_user(db:Session, user_in: UserCreate):
    hashed_password = hash_password(user_in.password)
    user = User(
        name=user_in.name,
        codeforces_handle=user_in.codeforces_handle,
        email=user_in.email,
        division=user_in.division,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def change_status(db: Session, handle: str, status: UserStatus):
    user = get_user_by_handle(db, handle)
    user.status = status
    db.commit()
    db.refresh()
    return user



def get_user_with_rating(db: Session, user_id: str):
    """
    Fetch a user and their current rating.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    rating = db.query(models.Rating).filter(models.Rating.user_id == user_id).first()
    return user, rating


def get_user_rating_history(db: Session, user_id: str):
    """
    Fetch rating history for a user (optional).
    """
    return (
        db.query(models.RatingHistory)
        .filter(models.RatingHistory.user_id == user_id)
        .order_by(models.RatingHistory.timestamp.asc())
        .all()
    )

def get_all_users(db: Session):
    return db.query(User).all()