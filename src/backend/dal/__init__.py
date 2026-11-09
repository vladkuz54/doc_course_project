import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DB_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://fleet:fleet@localhost:5432/fleet"
)

engine = create_async_engine(DB_URL, echo=False)

Session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
