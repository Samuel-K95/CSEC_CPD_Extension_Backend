from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user

from ..schemas import user_schemas

from ..crud import users
from ..db import get_db
from ..services.codeforces import verify_handle
from ..security import verify_password
import re

router = APIRouter(prefix="/api/users", tags=["user-auth"])

HANDLE_RE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')

@router.post("/register", response_model=user_schemas.UserRead, status_code=201)
def register(user_in: user_schemas.UserCreate, db: Session = Depends(get_db)):
    print("acepted request", user_in)
    handle = user_in.codeforces_handle
    print("checking regex...")
    if not HANDLE_RE.match(handle):
        raise HTTPException(status_code=400, detail="Invalid Codeforces handle format")

    print("checking if user exists in DB...")
    if users.get_user_by_handle(db, handle):
        raise HTTPException(status_code=400, detail="Codeforces handle already registered")

    print("calling verify_handle...")
    if not verify_handle(handle):
        raise HTTPException(status_code=400, detail="Codeforces handle does not exist")
    
    return users.create_user(db, user_in)

@router.post("/login", response_model=user_schemas.UserRead, status_code=200)
def login(user: user_schemas.UserLogin, db: Session = Depends(get_db)):
    user = users.get_user_by_handle(db, user.codeforces_handle)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user or not verify_password(user.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    return user_schemas.UserVerify(
        id=user.id,
        name=user.name,
        codeforces_handle=user.codeforces_handle,
        email=user.email,
        division=user.division,
        status=user.status,
        created_at=user.created_at,
        role=user.role,
        rating=user.rating
    )


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
        current_rating=rating.current_rating if rating else None,
        history=history
    )
