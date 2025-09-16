from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app import crud, schemas
from app.crud import users, ratings
from app.schemas import rating_schemas 

router = APIRouter(prefix="/rating", tags=["Rating"])

@router.get("/", response_model=list[rating_schemas.LeaderboardEntry])
def get_leaderboard(
    division: str | None = Query(None, description="Optional division filter"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard of all active users, optionally filtered by division.
    Sorted by current_rating desc and returns rank numbers.
    """
    results = ratings.get_leaderboard(db, division)

    # Assign ranks manually
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
