from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies.auth import require_admin, get_current_user
from app.crud import contests 
from app.schemas import contest_schemas, user_schemas
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
    # Return as Pydantic model
    return contest_schemas.ContestRead.from_orm(updated_contest)



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
    updated_contest = contests.remove_preparers_from_contest(db, contest_id, [user_id])
    if not updated_contest:
        raise HTTPException(status_code=404, detail="Preparer not found for this contest")
    # Return as Pydantic model (or a message if you prefer, but keep consistent with response_model)
    return contest_schemas.ContestRead.from_orm(updated_contest)

@router.get("/my", response_model=list[contest_schemas.ContestRead])
def list_my_contests(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List all contests the current user has participated in (attendance), or all contests if admin.
    """
    contests_list = contests.get_user_contests(db, current_user)
    return [contest_schemas.ContestRead.from_orm(contest) for contest in contests_list]

@router.get("/division/{division}", response_model=list[contest_schemas.ContestRead])
def get_contests_by_division(division: str, db: Session = Depends(get_db)):
    """
    Return all contests for a given division (e.g., 'Div1' or 'Div2').
    """
    print("request recieved for", division)
    contests_list = db.query(models.Contest).filter(models.Contest.division == str("".join(division))).all()
    reformated_contests = [contest_schemas.ContestRead.from_orm(contest) for contest in contests_list]
    return reformated_contests

@router.get("/preparers/{contest_id}", response_model=list[contest_schemas.ContestPreparers])
def get_contest_preparers(contest_id: str, db: Session = Depends(get_db)):
    """
    Return all preparers for a given contest.
    """
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    

    # get the preparers from the contest_preparers table
    filtered_preparers = (
        db.query(models.User)
        .join(models.contest_preparer_table, models.User.id == models.contest_preparer_table.c.user_id)
        .filter(models.contest_preparer_table.c.contest_id == contest_id)
        .all()
    )

    reformatted_preparers = [user_schemas.UserRead.from_orm(user) for user in filtered_preparers]

    # Print the user ids of the prepared preparers
    print("preparers are", reformatted_preparers, len(reformatted_preparers))

    return reformatted_preparers

@router.get("/{contest_id}", response_model=contest_schemas.ContestRead)
def get_contest_details(contest_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific contest by its ID.
    """
    contest = contests.get_contest(db, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest_schemas.ContestRead.from_orm(contest)