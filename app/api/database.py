"""
Database Configuration
======================

Sets up the SQLAlchemy engine, session factory, and declarative base.
Uses DATABASE_URL from environment (defaults to SQLite for local development).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# For SQLite, we need connect_args to allow multi-threaded access
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Normalize postgres:// to postgresql:// if needed
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # In SQLAlchemy 2.1+, postgresql:// defaults to psycopg (v3).
    # If psycopg is not installed but psycopg2 is present, fall back to postgresql+psycopg2://
    if DATABASE_URL.startswith("postgresql://"):
        try:
            import psycopg  # noqa: F401
        except ImportError:
            try:
                import psycopg2  # noqa: F401
                DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            except ImportError:
                pass

    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session when the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
