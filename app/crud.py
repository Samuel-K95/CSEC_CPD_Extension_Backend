from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate


def get_user_by_handle(db: Session, handle: str):
    return db.query(User).filter(User.codeforces_handle == handle).first()

def create_user(db:Session, user_in: UserCreate):
    user = User(
        name=user_in.name,
        codeforces_handle=user_in.codeforces_handle,
        email=user_in.email,
        division=user_in.division,
        rating=user_in.rating
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

