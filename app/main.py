from fastapi import FastAPI
from .db import Base, engine
from .routers import users
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CSEC Contest Rating - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CSEC Contest Rating Backend!"}