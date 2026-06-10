"""
Database initialization and session management for EcoTrace.
Uses SQLModel with SQLite — portable, file-based, no server needed.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./ecotrace.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables defined by SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan: initialize DB on startup."""
    init_db()
    yield
