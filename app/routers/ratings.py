from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.crud import users, ratings
from app.schemas import rating_schemas 
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/rating", tags=["Rating"])

@router.get("/", response_model=list[rating_schemas.LeaderboardEntry])
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get leaderboard of all active users, filtered by the current user's division (from token).
    Admins see all divisions.
    """
    try:
        if hasattr(current_user, "role") and getattr(current_user, "role", None) == "Admin":
            division = None
        else:
            division = getattr(current_user, "division", None)
        results = await ratings.get_leaderboard(db, division)

        leaderboard = []
        rank = 1
        for user, rating in results:
            leaderboard.append(
                rating_schemas.LeaderboardEntry(
                    rank=rank,
                    user_id=user.id,
                    name=user.name,
                    codeforces_handle=user.codeforces_handle,
                    division=user.division,
                    current_rating=rating.current_rating
                )
            )
            rank += 1

        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error getting leaderboard: {e}")
