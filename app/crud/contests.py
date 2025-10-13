from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from app.schemas import contest_schemas
from typing import List, Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
import datetime, asyncio


async def create_contest(db: AsyncSession, contest_in: contest_schemas.ContestCreate) -> models.Contest:
    result = await db.execute(select(models.Contest).filter(models.Contest.link == contest_in.link))
    existing = result.scalars().first()
    if existing:
        raise ValueError(f"Contest with link '{contest_in.link}' already exists.")
    contest_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    contest = models.Contest(
        name=contest_in.name,
        link=contest_in.link,
        division=contest_in.division,
        date=contest_date
    )
    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    

    for user_id in contest_in.preparer_ids or []:
        await db.execute(models.contest_preparer_table.insert().values(
            contest_id = contest.id,
            user_id = user_id,
            can_take_attendance = True
        ))

    await db.commit()
    return contest

async def get_contest(db: AsyncSession, contest_id: str) -> Optional[models.Contest]:
    result = await db.execute(
        select(models.Contest)
        .options(selectinload(models.Contest.preparers))
        .filter(models.Contest.id == contest_id)
    )
    return result.scalars().first()


async def add_preparers_to_contest(db: AsyncSession, contest_id: str, preparer_ids: List[str]) -> models.Contest:
    result = await db.execute(
        select(models.Contest).options(selectinload(models.Contest.preparers)).filter(models.Contest.id == contest_id)
    )
    contest = result.scalars().first()
    if not contest:
        raise ValueError("Contest not found")

    existing_ids = {p.id for p in contest.preparers}

    for user_id in preparer_ids:
        if user_id not in existing_ids:
            await db.execute(models.contest_preparer_table.insert().values(
                contest_id = contest.id,
                user_id = user_id,
                can_take_attendance = True
            ))

    await db.commit()
    await db.refresh(contest)
    return contest

async def remove_preparers_from_contest(db: AsyncSession, contest_id: str, preparer_ids: List[str]) -> models.Contest:
    """
    Remove a preparer from a contest.
    """
    result = await db.execute(select(models.Contest).filter(models.Contest.id == contest_id))
    contest = result.scalars().first()
    if not contest:
        raise ValueError("Contest not found")

    stmt = delete(models.contest_preparer_table).where(
        models.contest_preparer_table.c.contest_id == contest_id,
        models.contest_preparer_table.c.user_id.in_(preparer_ids)
    )
    await db.execute(stmt)
    await db.commit()
    await db.refresh(contest)
    return contest

async def get_user_contests(db: AsyncSession, user) -> list[models.Contest]:
    """
    Return all contests the user has participated in (attendance), or all contests if admin.
    """
    from app.models import UserRole, Contest, Attendance
    if user.role == UserRole.Admin:
        result = await db.execute(
            select(Contest)
            .options(selectinload(Contest.preparers))
        )
        return result.scalars().all()
    else:
        result = await db.execute(
            select(Contest)
            .options(selectinload(Contest.preparers))
            .join(Attendance, Contest.id == Attendance.contest_id)
            .filter(Attendance.user_id == str(user.id))
        )
        return result.scalars().all()
    

async def get_contests_by_division(db: AsyncSession, division: str) -> list[models.Contest]:
    """
    Return all contests for a given division (e.g., 'Div1' or 'Div2').
    """
    result = await db.execute(
        select(models.Contest)
        .options(selectinload(models.Contest.preparers))
        .filter(models.Contest.division == division)
    )
    return result.scalars().all()

async def update_contest_preparers(db: AsyncSession, contest_id: str, preparers: List[str]) -> models.Contest:
    """
    Update the preparers for a specific contest.
    """
    result = await db.execute(
        select(models.Contest)
        .options(selectinload(models.Contest.preparers))
        .filter(models.Contest.id == contest_id)
    )
    contest = result.scalars().first()
    if not contest:
        raise ValueError("Contest not found")

    # Remove all existing preparers
    stmt = delete(models.contest_preparer_table).where(
        models.contest_preparer_table.c.contest_id == contest_id
    )
    await db.execute(stmt)

    # Add new preparers
    for user_id in preparers:
        await db.execute(models.contest_preparer_table.insert().values(
            contest_id = contest.id,
            user_id = user_id,
            can_take_attendance = True
        ))

    await db.commit()
    await db.refresh(contest)
    return contest
