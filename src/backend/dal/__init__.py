import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///fleet.db")

engine = create_async_engine(DB_URL, echo=False)

if engine.dialect.name == "sqlite":

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


Session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
