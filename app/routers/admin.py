from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import user_schemas
from app.crud import users as crud_users
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