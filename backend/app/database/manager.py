"""
Runtime database connection manager. This is what section 4 of the design
doc calls for: the user should be able to configure a database connection
(type/host/port/db/user/password) OR upload a SQLite file OR just use the
demo database — from the running app, not only via .env at startup.

DatabaseManager owns the single "active" SQLAlchemy engine. Anything that
depends on the current database (the RAG index, the pipeline) registers an
on_change callback so it can rebuild itself when the user switches databases.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploaded"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEMO_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "demo_database" / "demo.db"


class ConnectionError_(Exception):
    """Raised when a proposed connection can't actually be established."""


@dataclass
class ConnectionInfo:
    kind: str    # demo | sqlite_upload | postgresql
    label: str   # human-readable: filename, or user@host:port/db


class DatabaseManager:
    def __init__(self) -> None:
        self._engine: Engine | None = None
        self._info = ConnectionInfo(kind="demo", label="Demo e-commerce database")
        self._listeners: list[Callable[[], None]] = []

    def on_change(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self.use_demo()
        return self._engine

    @property
    def info(self) -> ConnectionInfo:
        return self._info

    def use_demo(self) -> None:
        self._engine = create_engine(
            f"sqlite:///{DEMO_DB_PATH}", connect_args={"check_same_thread": False}
        )
        self._info = ConnectionInfo(kind="demo", label="Demo e-commerce database")
        self._notify()

    def use_csv_upload(self, file_bytes: bytes, original_filename: str) -> None:
        import csv
        import io
        import re
        import sqlite3

        # decode file
        text_content = None
        for enc in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
            try:
                text_content = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text_content is None:
            text_content = file_bytes.decode("utf-8", errors="replace")

        # sniffer / reader
        sample = text_content[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel

        reader = csv.reader(io.StringIO(text_content), dialect=dialect)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise ConnectionError_("Uploaded CSV is empty.")

        stem = Path(original_filename).stem
        table_name = re.sub(r"[^a-zA-Z0-9_]", "_", stem).strip("_").lower()
        if not table_name or table_name[0].isdigit():
            table_name = f"tbl_{table_name}"

        clean_headers = []
        for i, h in enumerate(raw_headers):
            c = re.sub(r"[^a-zA-Z0-9_]", "_", h.strip()).strip("_").lower()
            if not c:
                c = f"column_{i+1}"
            clean_headers.append(c)

        safe_name = f"{uuid.uuid4().hex}_{table_name}.sqlite"
        dest = UPLOAD_DIR / safe_name

        conn = sqlite3.connect(str(dest))
        cur = conn.cursor()
        col_defs = ", ".join(f'"{c}" TEXT' for c in clean_headers)
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        placeholders = ", ".join("?" for _ in clean_headers)
        rows_to_insert = []
        for row in reader:
            if not row or all(c.strip() == "" for c in row):
                continue
            if len(row) < len(clean_headers):
                row = row + [""] * (len(clean_headers) - len(row))
            else:
                row = row[:len(clean_headers)]
            rows_to_insert.append(row)

        if rows_to_insert:
            cur.executemany(f'INSERT INTO "{table_name}" VALUES ({placeholders})', rows_to_insert)
        conn.commit()
        conn.close()

        engine = create_engine(f"sqlite:///{dest}", connect_args={"check_same_thread": False})
        self._engine = engine
        self._info = ConnectionInfo(kind="sqlite_upload", label=original_filename)
        self._notify()

    def use_file_upload(self, file_bytes: bytes, original_filename: str) -> None:
        lower = original_filename.lower()
        if lower.endswith(".csv"):
            self.use_csv_upload(file_bytes, original_filename)
        elif lower.endswith((".db", ".sqlite", ".sqlite3")):
            self.use_sqlite_upload(file_bytes, original_filename)
        else:
            raise ConnectionError_(f"Unsupported file format: {original_filename}. Please upload a .sqlite, .db, or .csv file.")

    def use_sqlite_upload(self, file_bytes: bytes, original_filename: str) -> None:
        if original_filename.lower().endswith(".csv"):
            return self.use_csv_upload(file_bytes, original_filename)

        safe_name = f"{uuid.uuid4().hex}_{Path(original_filename).name}"
        dest = UPLOAD_DIR / safe_name
        dest.write_bytes(file_bytes)

        engine = create_engine(f"sqlite:///{dest}", connect_args={"check_same_thread": False})
        try:
            with engine.connect() as conn:
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
        except Exception as e:
            dest.unlink(missing_ok=True)
            raise ConnectionError_(f"Uploaded file is not a valid SQLite database: {e}") from e

        if not tables:
            dest.unlink(missing_ok=True)
            raise ConnectionError_("Uploaded SQLite file has no tables.")

        self._engine = engine
        self._info = ConnectionInfo(kind="sqlite_upload", label=original_filename)
        self._notify()


    def use_postgres(self, host: str, port: int, database: str, user: str, password: str) -> None:
        try:
            import psycopg2  # noqa: F401
        except ImportError as e:
            raise ConnectionError_(
                "PostgreSQL support requires psycopg2-binary. Run "
                "`pip install psycopg2-binary` in the backend environment and try again."
            ) from e

        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise ConnectionError_(f"Could not connect to PostgreSQL: {e}") from e

        self._engine = engine
        self._info = ConnectionInfo(kind="postgresql", label=f"{user}@{host}:{port}/{database}")
        self._notify()


# Process-wide singleton — one active connection per running backend, which
# matches the single-session demo use case. For multi-tenant use, key this
# by session_id instead.
database_manager = DatabaseManager()
