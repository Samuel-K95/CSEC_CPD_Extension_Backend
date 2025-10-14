import datetime, asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.crud import users as crud_users
from app.crud import refresh_tokens as crud_refresh
from app.security import (
    create_access_token, create_refresh_token, verify_password
)
from fastapi.concurrency import run_in_threadpool
from app.config import settings
from app.schemas import user_schemas
from app.dependencies.auth import get_current_user
from app import models
from datetime import timedelta
from jose import jwt, JWTError
import re


# Schema for refresh token request
from pydantic import BaseModel

from app.services.codeforces import verify_handle

class RefreshTokenRequest(BaseModel):
    refresh_token: str

router = APIRouter(prefix="/api/auth", tags=["authentication"])

HANDLE_RE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')

@router.post("/login", response_model=user_schemas.UserLogin)
async def login_user(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await crud_users.get_user_by_handle(db, handle=form_data.username)
        if not user or not await run_in_threadpool(verify_password, form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.codeforces_handle})
        refresh_token_str = create_refresh_token(data={"sub": user.codeforces_handle})
        
        # Store refresh token in DB
        await crud_refresh.create_refresh_token(
            db=db, 
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error during login: {e}")


@router.post("/refresh", response_model=user_schemas.Token)
async def refresh_access_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        refresh_token = req.refresh_token
        db_token = await crud_refresh.get_refresh_token(db, token=refresh_token)
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = await crud_users.get_user_by_handle(db, handle=username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Revoke the old refresh token
        await crud_refresh.revoke_refresh_token(db, token=refresh_token)

        # Issue new tokens
        new_access_token = create_access_token(data={"sub": user.codeforces_handle})
        new_refresh_token = create_refresh_token(data={"sub": user.codeforces_handle})

        await crud_refresh.create_refresh_token(
            db,
            user_id=user.id,
            token=new_refresh_token,
            expires_in=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error during token refresh: {e}")


@router.post("/register", response_model=user_schemas.UserRead, status_code=201)
async def register(user_in: user_schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        handle = user_in.codeforces_handle
        if not HANDLE_RE.match(handle):
            raise HTTPException(status_code=400, detail="Invalid Codeforces handle format")

        if await crud_users.get_user_by_handle(db, handle):
            raise HTTPException(status_code=400, detail="Codeforces handle already registered")

        if not await verify_handle(handle):
            raise HTTPException(status_code=400, detail="Codeforces handle does not exist")
        
        return await crud_users.create_user(db, user_in)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error during user registration: {e}")
