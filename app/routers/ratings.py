from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app import crud, schemas
from app.crud import users, ratings
from app.schemas import rating_schemas 
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/rating", tags=["Rating"])

@router.get("/", response_model=list[rating_schemas.LeaderboardEntry])
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get leaderboard of all active users, filtered by the current user's division (from token).
    Admins see all divisions.
    """

    if hasattr(current_user, "role") and getattr(current_user, "role", None) == "Admin":
        division = None
    else:
        division = getattr(current_user, "division", None)
    print("current user", current_user)
    results = ratings.get_leaderboard(db, division)

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
