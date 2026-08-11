"""Database layer — optional Postgres persistence for foresight tracking.

Activated when DATABASE_URL is set.  Otherwise the engine runs purely in-memory.
"""
from __future__ import annotations

import os
from typing import Optional

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        url = os.environ.get("DATABASE_URL")
        if not url:
            return None
        _engine = create_engine(url, pool_pre_ping=True, pool_size=5)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None
        from sqlalchemy.orm import sessionmaker
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def get_session():
    factory = get_session_factory()
    if factory is None:
        return None
    return factory()


def init_db():
    engine = get_engine()
    if engine is None:
        return False
    from earth1.db.models import Base
    Base.metadata.create_all(bind=engine)
    return True


def is_enabled() -> bool:
    return bool(os.environ.get("DATABASE_URL"))
