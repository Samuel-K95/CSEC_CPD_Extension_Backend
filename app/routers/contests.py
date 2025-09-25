from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies.auth import require_admin, get_current_user
from app.crud import contests 
from app.schemas import contest_schemas
from app.models import UserRole
from app import models

router = APIRouter(prefix="/api/contests", tags=["contests"])

@router.post("/", response_model=contest_schemas.ContestRead, status_code=status.HTTP_201_CREATED)
def create_contest(
    contest_in: contest_schemas.ContestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    print("hitting create contest endpoint", contest_in)
    """
    Admin-only: Create a new contest and (optionally) assign one or more preparers.
    """
    contest_obj = contests.create_contest(db, contest_in)
    return contest_schemas.ContestRead.from_orm(contest_obj)

@router.post("/{contest_id}/assign-preparers", response_model=contest_schemas.ContestRead)
def assign_preparers(
    contest_id: str,
    body: contest_schemas.AssignPreparersRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Assign one or more preparers to an existing contest.
    """
    try:
        updated_contest = contests.add_preparers_to_contest(db, contest_id, body.preparer_ids)

    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return updated_contest



@router.delete("/{contest_id}/preparers/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_preparer(
    contest_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin)
):
    """
    Admin-only: Revoke a user's preparer access for a specific contest.
    """
    success = contests.remove_preparers_from_contest(db, contest_id, [user_id])
    if not success:
        raise HTTPException(status_code=404, detail="Preparer not found for this contest")

    return {"message": "Preparer access revoked successfully"}

@router.get("/my", response_model=list[contest_schemas.ContestRead])
def list_my_contests(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List all contests the current user has participated in (attendance), or all contests if admin.
    """
    contests_list = contests.get_user_contests(db, current_user)
    return [contest_schemas.ContestRead.from_orm(contest) for contest in contests_list]
