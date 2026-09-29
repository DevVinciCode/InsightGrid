"""
DatabaseProvider: one small interface, two implementations (SQLite, Postgres).
Swap providers via .env (DB_TYPE) — no other code needs to change.
"""
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config.settings import Settings


def build_engine(settings: Settings) -> Engine:
    """Create the SQLAlchemy engine for whichever DB_TYPE is configured."""
    if settings.DB_TYPE == "sqlite":
        db_path = Path(__file__).resolve().parents[3] / "data" / "demo_database" / "demo.db"
        # allow an absolute/relative override via DB_PATH if it points elsewhere
        if settings.DB_PATH and settings.DB_PATH != "../data/demo_database/demo.db":
            db_path = Path(settings.DB_PATH)
        return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    if settings.DB_TYPE == "postgresql":
        url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        return create_engine(url, pool_pre_ping=True)

    raise ValueError(f"Unsupported DB_TYPE: {settings.DB_TYPE}")
