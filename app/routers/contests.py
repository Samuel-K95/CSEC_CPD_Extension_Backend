from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies.auth import require_admin, get_current_user
from app.crud import contests 
from app.schemas import contest_schemas, user_schemas
from app import models
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/contests", tags=["contests"])

@router.post("/", response_model=contest_schemas.ContestRead, status_code=status.HTTP_201_CREATED)
async def create_contest(
    contest_in: contest_schemas.ContestCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    print("hitting create contest endpoint", contest_in)
    """
    Admin-only: Create a new contest and (optionally) assign one or more preparers.
    """
    try:
        contest_obj = await contests.create_contest(db, contest_in)
        return contest_schemas.ContestRead.from_orm(contest_obj)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error creating contest: {e}")

@router.post("/{contest_id}/assign-preparers", response_model=contest_schemas.ContestRead)
async def assign_preparers(
    contest_id: str,
    body: contest_schemas.AssignPreparersRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Admin-only: Assign one or more preparers to an existing contest.
    """
    try:
        updated_contest = await contests.add_preparers_to_contest(db, contest_id, body.preparer_ids)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error assigning preparers: {e}")
    # Return as Pydantic model
    return contest_schemas.ContestRead.from_orm(updated_contest)


@router.get("/my", response_model=list[contest_schemas.ContestRead])
async def list_my_contests(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """
    List all contests the current user has participated in (attendance), or all contests if admin.
    """
    try:
        contests_list = await contests.get_user_contests(db, current_user)
        return [contest_schemas.ContestRead.from_orm(contest) for contest in contests_list]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error listing user contests: {e}")

@router.get("/division/{division}", response_model=list[contest_schemas.ContestRead])
async def get_contests_by_division(division: str, db: AsyncSession = Depends(get_db)):
    """
    Return all contests for a given division (e.g., 'Div1' or 'Div2').
    """
    print("request recieved for", division)
    try:
        result = await db.execute(
            select(models.Contest)
            .options(selectinload(models.Contest.preparers))
            .filter(models.Contest.division == division)
        )
        contests_list = result.scalars().all()
        reformated_contests = [contest_schemas.ContestRead.from_orm(contest) for contest in contests_list]
        return reformated_contests
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error getting contests by division: {e}")

@router.get("/preparers/{contest_id}", response_model=list[contest_schemas.ContestPreparers])
async def get_contest_preparers(contest_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return all preparers for a given contest.
    """
    try:
        result = await db.execute(select(models.Contest).filter(models.Contest.id == contest_id))
        contest = result.scalars().first()
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        

        # get the preparers from the contest_preparers table
        result = await db.execute(
            select(models.User)
            .join(models.contest_preparer_table, models.User.id == models.contest_preparer_table.c.user_id)
            .filter(models.contest_preparer_table.c.contest_id == contest_id)
        )
        filtered_preparers = result.scalars().all()

        reformatted_preparers = [user_schemas.UserRead.from_orm(user) for user in filtered_preparers]

        # Print the user ids of the prepared preparers
        print("preparers are", reformatted_preparers, len(reformatted_preparers))

        return reformatted_preparers
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error getting contest preparers: {e}")

@router.get("/{contest_id}", response_model=contest_schemas.ContestRead)
async def get_contest_details(contest_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific contest by its ID.
    """
    try:
        contest = await contests.get_contest(db, contest_id)
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        return contest_schemas.ContestRead.from_orm(contest)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error getting contest details: {e}")