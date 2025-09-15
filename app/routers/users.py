from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db import get_db
from ..services.codeforces import verify_handle
import re

router = APIRouter(prefix="/api/users", tags=["users"])

HANDLE_RE = re.compile(r'^[A-Za-z0-9_-]{1,100}$')

@router.post("/register", response_model=schemas.UserRead, status_code=201)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    print("acepted request", user_in)
    handle = user_in.codeforces_handle
    print("checking regex...")
    if not HANDLE_RE.match(handle):
        raise HTTPException(status_code=400, detail="Invalid Codeforces handle format")

    print("checking if user exists in DB...")
    if crud.get_user_by_handle(db, handle):
        raise HTTPException(status_code=400, detail="Codeforces handle already registered")

    print("calling verify_handle...")
    if not verify_handle(handle):
        raise HTTPException(status_code=400, detail="Codeforces handle does not exist")

    
    return crud.create_user(db, user_in)