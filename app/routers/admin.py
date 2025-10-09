from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import contest_schemas, user_schemas
from app.crud import contests, users as crud_users
from typing import List
from app.dependencies.auth import require_admin, get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])



@router.get("/users/{division}", status_code=status.HTTP_200_OK, response_model=List[user_schemas.UserRead])
def get_users_by_division(
    division: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Return all users in the specified division.
    """
    users_list = crud_users.get_users_by_division(db, division)
    return users_list


@router.patch("/users/{handle}/status", response_model=user_schemas.UserRead)
def change_user_status_admin(
    handle: str,
    body: user_schemas.ChangeStatusandRole,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Change a user's status (e.g., Active, Inactive, Banned).
    """
    user = crud_users.get_user_by_handle(db, handle)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = crud_users.change_status_and_role(db, handle, body.status, body.role)

    return updated_user


@router.get("/contests/division/{division}", response_model=List[contest_schemas.ContestRead])
def get_contests_by_division(
    division: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Get all contests in a specific division.
    """
    contests_list = contests.get_contests_by_division(db, division)
    return contests_list



@router.delete("/contests/{contest_id}/preparers/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_preparer(
    contest_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(require_admin)
):
    """
    Admin-only: Revoke a user's preparer access for a specific contest.
    """
    updated_contest = contests.remove_preparers_from_contest(db, contest_id, [user_id])
    if not updated_contest:
        raise HTTPException(status_code=404, detail="Preparer not found for this contest")
    # Return as Pydantic model (or a message if you prefer, but keep consistent with response_model)
    return contest_schemas.ContestRead.from_orm(updated_contest)


@router.patch("/contests/{contest_id}/preparers", response_model=contest_schemas.ContestRead)
def update_contest_preparers(
    contest_id: str,
    body: contest_schemas.ContestUpdatePreparers,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Update the preparers for a specific contest.
    """
    contest = contests.get_contest(db, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    updated_contest = contests.update_contest_preparers(db, contest_id, body.preparers)
    return updated_contest