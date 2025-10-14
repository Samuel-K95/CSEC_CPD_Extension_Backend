from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Division, User, UserStatus
from ..schemas.user_schemas import UserCreate
from ..security import hash_password
from fastapi.concurrency import run_in_threadpool
from app import models


async def get_user_by_handle(db: AsyncSession, handle: str):
    db.sync_session.expire_on_commit = False
    result = await db.execute(select(User).filter(User.codeforces_handle == handle))
    return result.scalars().first()

async def get_users_by_division(db: AsyncSession, division: str):
    result = await db.execute(select(User).filter(User.division == division))
    return result.scalars().all()

async def create_user(db: AsyncSession, user_in: UserCreate):
    hashed_password = await run_in_threadpool(hash_password, user_in.password)
    user = User(
        name=user_in.name,
        codeforces_handle=user_in.codeforces_handle,
        email=user_in.email,
        division=user_in.division,
        hashed_password=hashed_password
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def change_status_role_and_division(db: AsyncSession, handle: str, status: UserStatus, role: str, division: Division):
    user = await get_user_by_handle(db, handle)
    user.status = status
    user.role = role
    user.division = division    
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_with_rating(db: AsyncSession, user_id: int):
    """
    Fetch a user and their current rating.
    """
    user_result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        return None, None

    rating_result = await db.execute(select(models.Rating).filter(models.Rating.user_id == user_id))
    rating = rating_result.scalars().first()
    return user, rating


async def get_user_rating_history(db: AsyncSession, user_id: int):
    """
    Fetch rating history for a user (optional).
    """
    result = await db.execute(
        select(models.RatingHistory)
        .filter(models.RatingHistory.user_id == user_id)
        .order_by(models.RatingHistory.timestamp.asc())
    )
    return result.scalars().all()

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def update_user(db: AsyncSession, user_id: int, updates: dict):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None

    for key, value in updates.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    if 'password' in updates and updates['password']:
        user.hashed_password = await run_in_threadpool(hash_password, updates['password'])

    await db.commit()
    await db.refresh(user)
    return user