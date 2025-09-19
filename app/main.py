from fastapi import FastAPI

from app.routers import attendance, contests, ratings, auth
from .db import Base, engine
from .routers import users
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CSEC Contest Rating - Backend")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(users.router)
app.include_router(ratings.router)
app.include_router(contests.router)
app.include_router(attendance.router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CSEC Contest Rating Backend!"}