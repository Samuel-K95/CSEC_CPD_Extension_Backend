from sqlalchemy.orm import Session
from app import models
from datetime import datetime, timedelta

def create_refresh_token(db: Session, user_id: int, token: str, expires_in: timedelta) -> models.RefreshToken:
    expires_at = datetime.utcnow() + expires_in
    db_token = models.RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_refresh_token(db: Session, token: str) -> models.RefreshToken | None:
    return db.query(models.RefreshToken).filter(models.RefreshToken.token == token).first()

def revoke_refresh_token(db: Session, token: str):
    db_token = get_refresh_token(db, token)
    if db_token:
        db_token.is_revoked = True
        db.commit()
