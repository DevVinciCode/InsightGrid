"""
Discovers tables, columns, types, keys, relationships, and lightweight
statistics from the connected database. This metadata feeds both the RAG
document builder and the SQL validator.

Example output shape (per table):
{
  "table": "orders",
  "row_count": 5680,
  "columns": [{"name": "order_id", "type": "INTEGER", "primary_key": true,
               "nullable": False, "sample_values": [1, 2, 3]}, ...],
  "foreign_keys": [{"column": "customer_id", "ref_table": "customers",
                     "ref_column": "customer_id"}]
}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


@dataclass
class ColumnMeta:
    name: str
    type: str
    primary_key: bool
    nullable: bool
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class ForeignKeyMeta:
    column: str
    ref_table: str
    ref_column: str


@dataclass
class TableMeta:
    table: str
    row_count: int
    columns: list[ColumnMeta]
    foreign_keys: list[ForeignKeyMeta]
    description: str = ""


# Hand-written table/column descriptions. In a real deployment these would be
# editable by the DB admin (or inferred once and cached) — kept simple here.
TABLE_DESCRIPTIONS = {
    "orders": "Stores individual customer purchase transactions, one row per order.",
    "customers": "Stores customer profile information: location and segment.",
    "products": "Stores product catalog information: category and price.",
}

# Business/semantic definitions the RAG layer should know about. This is the
# "semantic knowledge" layer described in the design doc — kept as plain data
# so it's trivial to extend without touching code.
SEMANTIC_NOTES = [
    "Revenue means completed transaction value: orders.revenue where orders.status = 'completed'.",
    "Profit is orders.profit, only meaningful for completed orders.",
    "Cancelled and returned orders should normally be excluded from revenue and profit totals "
    "unless the user explicitly asks about cancellations or returns.",
    "A customer's 'city' and 'state' come from the customers table, not orders.",
    "Time-based questions (monthly, yearly, trend) should use orders.order_date.",
]


def extract_schema(engine: Engine, sample_size: int = 3) -> list[TableMeta]:
    inspector = inspect(engine)
    tables: list[TableMeta] = []

    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            pk_cols = set(inspector.get_pk_constraint(table_name).get("constrained_columns") or [])
            fks = [
                ForeignKeyMeta(
                    column=fk["constrained_columns"][0],
                    ref_table=fk["referred_table"],
                    ref_column=fk["referred_columns"][0],
                )
                for fk in inspector.get_foreign_keys(table_name)
                if fk.get("constrained_columns") and fk.get("referred_columns")
            ]

            columns = []
            for col in inspector.get_columns(table_name):
                sample_values = []
                try:
                    rows = conn.execute(
                        text(f'SELECT DISTINCT "{col["name"]}" FROM "{table_name}" '
                             f'WHERE "{col["name"]}" IS NOT NULL LIMIT :n'),
                        {"n": sample_size},
                    ).fetchall()
                    sample_values = [r[0] for r in rows]
                except Exception:
                    pass  # sampling is best-effort only

                columns.append(ColumnMeta(
                    name=col["name"],
                    type=str(col["type"]),
                    primary_key=col["name"] in pk_cols,
                    nullable=col.get("nullable", True),
                    sample_values=sample_values,
                ))

            try:
                row_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
            except Exception:
                row_count = -1

            tables.append(TableMeta(
                table=table_name,
                row_count=row_count,
                columns=columns,
                foreign_keys=fks,
                description=TABLE_DESCRIPTIONS.get(table_name, ""),
            ))

    return tables
