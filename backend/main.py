from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import asyncpg
from database import init_db, get_db, engine, Base
from contextlib import asynccontextmanager
import models
from sqlalchemy import text
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "https://spotify-visualizer-tau.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# world hello
@app.get("/")
async def read_root():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = 'failed:' + str(e)

    return {
            "status": "ok, backend connected to front",
            "environment": ENVIRONMENT,
            "db": db_status
            }
