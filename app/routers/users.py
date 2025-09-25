from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user

from ..schemas import user_schemas

from ..crud import users
from ..db import get_db
from ..services.codeforces import verify_handle
from ..security import verify_password
import re

router = APIRouter(prefix="/api/users", tags=["users"])

@router.patch("/{handle}", response_model=user_schemas.UserRead)
def change_user_status(handle: str, body: user_schemas.ChangeStatusRequest, db: Session = Depends(get_db)):
    user = users.get_user_by_handle(db, handle)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = users.change_status(db, handle, body.status)

    return updated_user

@router.get("/profile", response_model=user_schemas.UserProfile)
def get_me(
    include_history: bool = Query(False, description="Include rating history if true"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current user's profile, rating, and optionally rating history.
    """
    user, rating = users.get_user_with_rating(db, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    history = None
    if include_history:
        history = users.get_user_rating_history(db, current_user.id)

    return user_schemas.UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        codeforces_handle=user.codeforces_handle,
        division=user.division,
        role=user.role,
        current_rating=user.rating,
        history=history
    )

@router.get("/all", response_model=list[user_schemas.UserRead])
def get_all_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Return all users in the database. Requires authentication.
    """
    users_list = users.get_all_users(db)
    return users_list
