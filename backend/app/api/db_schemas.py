from __future__ import annotations

from pydantic import BaseModel


class PostgresConnectRequest(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str


class TableSummary(BaseModel):
    name: str
    row_count: int
    column_count: int
    columns: list[str] = []


class DatabaseStatusResponse(BaseModel):
    kind: str
    label: str
    tables: list[str]
    table_summaries: list[TableSummary] = []
    total_rows: int = 0

