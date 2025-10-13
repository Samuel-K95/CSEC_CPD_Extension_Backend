from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from datetime import datetime, timedelta, timezone

async def create_refresh_token(db: AsyncSession, user_id: int, token: str, expires_in: timedelta) -> models.RefreshToken:
    expires_at_aware = datetime.now(timezone.utc) + expires_in
    expires_at_naive = expires_at_aware.replace(tzinfo=None)
    
    created_at_aware = datetime.now(timezone.utc)
    created_at_naive = created_at_aware.replace(tzinfo=None)
    
    db_token = models.RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at_naive,
        created_at=created_at_naive
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token

async def get_refresh_token(db: AsyncSession, token: str) -> models.RefreshToken | None:
    result = await db.execute(select(models.RefreshToken).filter(models.RefreshToken.token == token))
    return result.scalars().first()

async def revoke_refresh_token(db: AsyncSession, token: str):
    db_token = await get_refresh_token(db, token)
    if db_token:
        db_token.is_revoked = True
        await db.commit()
