"""Database configuration and connection management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from app.config.settings import settings

# Create database engine
# Note: StaticPool is mainly for SQLite, for PostgreSQL we should use QueuePool
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=settings.sql_echo,  # Use separate SQL echo setting
        connect_args={"check_same_thread": False}  # Only for SQLite
    )
else:
    # For PostgreSQL and other databases
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_size=5,        # Number of connections to maintain
        max_overflow=10,    # Additional connections allowed
        echo=settings.sql_echo,  # Use separate SQL echo setting
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Don't expire objects after commit
)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Get database session as context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections."""
    engine.dispose()
