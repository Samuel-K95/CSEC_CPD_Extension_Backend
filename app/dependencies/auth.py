from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from app.db import get_db
from sqlalchemy import select
from typing import Optional
from dotenv import load_dotenv
import os

from app.config import settings
from app.schemas import user_schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    """
    Decode JWT token and fetch current user from DB.
    """

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = user_schemas.TokenData(username=username)
    except JWTError:
        raise credential_exception

    result = await db.execute(select(models.User).filter(models.User.codeforces_handle == token_data.username))
    user = result.scalars().first()
    if user is None:
        raise credential_exception
    return user

async def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to ensure the current user is an admin.
    Raises 403 if current user is not admin
    """
    if current_user.role != models.UserRole.Admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires admin privileges",
        )
    return current_user


async def require_preparer(
        contest_id: str,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> models.User:
    """
    Checks if the current user is a preparer for the given contest.
    """

    # Admins can always take attendance
    if current_user.role == models.UserRole.Admin:
        return current_user
    
    # Check contest_preparer_table for user access
    stmt = select(models.contest_preparer_table).where(
        models.contest_preparer_table.c.contest_id == contest_id,
        models.contest_preparer_table.c.user_id == current_user.id,
        models.contest_preparer_table.c.can_take_attendance == True
    )

    result = await db.execute(stmt)
    auth_check = result.first()

    if not auth_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized to take attendance for this contest",
        )

    return current_user
