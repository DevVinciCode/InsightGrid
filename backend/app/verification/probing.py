"""
STAGE 3 SCAFFOLD — NOT YET WIRED INTO THE MAIN PIPELINE.

Safe, read-only exploratory queries used to gather evidence when the system
is uncertain about a question's meaning (design doc section 8), e.g. checking
which numeric columns actually vary meaningfully before guessing which one
"performing poorly" refers to.

Reuses database/executor.py's safety guarantees (SELECT-only, row-capped,
forbidden-keyword blocked) — probing must never bypass those. This module
only adds a probe-specific row limit (PROBE_ROW_LIMIT) and a small library of
canned, safe exploratory queries.

Wiring plan: called from intent/clarification.py's INVESTIGATE branch, with
the probe's result fed back into a second decide() call before falling back
to ASK.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from app.database.executor import ExecutionResult, execute_safe


def probe_column_variance(engine: Engine, table: str, column: str, row_limit: int = 20) -> ExecutionResult:
    """Example probe: sample a numeric column's spread to check if it's a plausible metric."""
    sql = f'SELECT MIN("{column}") AS min_val, MAX("{column}") AS max_val, AVG("{column}") AS avg_val FROM "{table}"'
    return execute_safe(engine, sql, row_limit=row_limit)


def probe_distinct_values(engine: Engine, table: str, column: str, row_limit: int = 20) -> ExecutionResult:
    """Example probe: sample distinct values of a categorical column."""
    sql = f'SELECT DISTINCT "{column}" FROM "{table}" LIMIT {row_limit}'
    return execute_safe(engine, sql, row_limit=row_limit)
