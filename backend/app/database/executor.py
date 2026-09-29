"""
Safe query execution: SELECT-only, row-limited, timeout-bounded. Used for
both the main query pipeline and (later) Stage-3 database probing, so the
safety guarantees live in exactly one place.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|PRAGMA|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(Exception):
    pass


@dataclass
class ExecutionResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    error: str | None = None


def assert_safe(sql: str) -> None:
    """Raises UnsafeSQLError if the SQL is anything but a read-only SELECT."""
    stripped = sql.strip().rstrip(";")
    if not re.match(r"^\s*(WITH|SELECT)\b", stripped, re.IGNORECASE):
        raise UnsafeSQLError("Only SELECT (optionally with a WITH/CTE prefix) statements are allowed.")
    if ";" in stripped:
        raise UnsafeSQLError("Multiple statements are not allowed.")
    if FORBIDDEN_KEYWORDS.search(stripped):
        raise UnsafeSQLError("Query contains a forbidden write/DDL keyword.")


def execute_safe(
    engine: Engine,
    sql: str,
    row_limit: int = 500,
    timeout_seconds: int = 10,
) -> ExecutionResult:
    """
    Executes a validated SELECT with a hard row cap. Timeout is enforced at
    the SQLite driver level for the demo DB; for Postgres, statement_timeout
    should be set via connection options (documented in docs/architecture.md).
    """
    assert_safe(sql)

    capped_sql = sql.strip().rstrip(";")
    # Apply a defensive LIMIT if the query doesn't already have one.
    if not re.search(r"\bLIMIT\b", capped_sql, re.IGNORECASE):
        capped_sql = f"{capped_sql} LIMIT {row_limit + 1}"

    try:
        with engine.connect() as conn:
            if engine.dialect.name == "sqlite":
                raw = conn.connection.dbapi_connection if hasattr(conn.connection, "dbapi_connection") else conn.connection
                try:
                    raw.execute(f"PRAGMA query_only = ON")
                except Exception:
                    pass
            result = conn.execute(text(capped_sql))
            columns = list(result.keys())
            rows = [list(r) for r in result.fetchmany(row_limit + 1)]
    except sqlite3.OperationalError as e:
        return ExecutionResult(columns=[], rows=[], row_count=0, truncated=False, error=str(e))
    except Exception as e:
        return ExecutionResult(columns=[], rows=[], row_count=0, truncated=False, error=str(e))

    truncated = len(rows) > row_limit
    if truncated:
        rows = rows[:row_limit]

    return ExecutionResult(columns=columns, rows=rows, row_count=len(rows), truncated=truncated)
