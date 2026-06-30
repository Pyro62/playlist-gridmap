from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db(): # initialize
    async with engine.begin() as conn: #begin() commits on exit if no error vs connect() needs manual execute
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session: # make session with sessionlocal, give a session and pause, when close then clean up with async with
        yield session


