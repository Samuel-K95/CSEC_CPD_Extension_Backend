from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.crud import users, refresh_tokens as crud_refresh
from app.security import (
    create_access_token, create_refresh_token, verify_password
)
from app.config import settings
from app.db import get_db
from app.schemas import user_schemas


# Schema for refresh token request
from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    refresh_token: str
from app.services.codeforces import verify_handle
from datetime import timedelta, datetime
import re

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/login", response_model=user_schemas.UserLogin)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = users.get_user_by_handle(db, handle=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.codeforces_handle})
    refresh_token_str = create_refresh_token(data={"sub": user.codeforces_handle})
    
    # Store refresh token in DB
    crud_refresh.create_refresh_token(
        db, 
        user_id=user.id, 
        token=refresh_token_str, 
        expires_in=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return ({
        "id": user.id,
        "access_token": access_token, 
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
        "codeforces_handle": user.codeforces_handle,
        "role": user.role,
        "division": user.division,
        "name": user.name,
        "email": user.email,
        "current_rating": user.rating
    })


@router.post("/refresh", response_model=user_schemas.Token)
def refresh_access_token(
    req: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    refresh_token = req.refresh_token
    db_token = crud_refresh.get_refresh_token(db, token=refresh_token)
    if not db_token or db_token.is_revoked or db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = users.get_user_by_handle(db, handle=username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Revoke the old refresh token
    crud_refresh.revoke_refresh_token(db, token=refresh_token)

    # Issue new tokens
    new_access_token = create_access_token(data={"sub": user.codeforces_handle})
    new_refresh_token = create_refresh_token(data={"sub": user.codeforces_handle})

    crud_refresh.create_refresh_token(
        db,
        user_id=user.id,
        token=new_refresh_token,
        expires_in=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


HANDLE_RE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')

@router.post("/register", response_model=user_schemas.UserRead, status_code=201)
def register(user_in: user_schemas.UserCreate, db: Session = Depends(get_db)):
    handle = user_in.codeforces_handle
    if not HANDLE_RE.match(handle):
        raise HTTPException(status_code=400, detail="Invalid Codeforces handle format")

    if users.get_user_by_handle(db, handle):
        raise HTTPException(status_code=400, detail="Codeforces handle already registered")

    if not verify_handle(handle):
        raise HTTPException(status_code=400, detail="Codeforces handle does not exist")
    
    return users.create_user(db, user_in)
