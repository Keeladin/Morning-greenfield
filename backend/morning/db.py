from __future__ import annotations

from sqlalchemy import Engine, create_engine


def create_database_engine(database_url: str) -> Engine:
    if not database_url:
        raise ValueError("database_url is required")
    return create_engine(database_url, pool_pre_ping=True)
