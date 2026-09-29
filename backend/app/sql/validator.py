"""
Multi-level SQL validation, run before execution:

  1. syntax   — does it parse?
  2. safety   — read-only, single statement, no forbidden keywords
  3. schema   — do referenced tables/columns exist?
  4. join     — are joins based on real foreign-key relationships?
  5. semantic — does the SQL actually match the analytical intent
               (e.g. a "top N" request without ORDER BY is incomplete)?

Each level returns a ValidationIssue list; callers decide whether to block
execution (safety/syntax) or just warn (semantic).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from app.database.executor import assert_safe, UnsafeSQLError
from app.database.schema_extractor import TableMeta
from app.models.intent import AnalyticalIntent


@dataclass
class ValidationIssue:
    level: str       # syntax | safety | schema | join | semantic
    severity: str    # error | warning
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_blocking_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def add(self, level: str, severity: str, message: str) -> None:
        self.issues.append(ValidationIssue(level=level, severity=severity, message=message))


def validate_sql(sql: str, tables: list[TableMeta], intent: AnalyticalIntent) -> ValidationReport:
    report = ValidationReport()

    # 1. Safety (blocking)
    try:
        assert_safe(sql)
    except UnsafeSQLError as e:
        report.add("safety", "error", str(e))
        return report  # no point parsing further if it's unsafe

    # 2. Syntax (blocking)
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
    except Exception as e:
        report.add("syntax", "error", f"SQL failed to parse: {e}")
        return report

    # 3. Schema check (blocking) — every referenced table/column must exist
    known_tables = {t.table.lower(): {c.name.lower() for c in t.columns} for t in tables}
    referenced_tables = {t.name.lower() for t in parsed.find_all(exp.Table)}
    for tname in referenced_tables:
        if tname not in known_tables:
            report.add("schema", "error", f"Table '{tname}' does not exist in the schema.")

    referenced_columns = [c for c in parsed.find_all(exp.Column)]
    all_known_columns = {col for cols in known_tables.values() for col in cols}
    for col in referenced_columns:
        col_name = col.name.lower()
        if col_name == "*":
            continue
        table_hint = col.table.lower() if col.table else None
        if table_hint and table_hint in known_tables:
            if col_name not in known_tables[table_hint]:
                report.add("schema", "error",
                           f"Column '{col_name}' does not exist on table '{table_hint}'.")
        elif not table_hint and col_name not in all_known_columns:
            report.add("schema", "warning",
                       f"Column '{col_name}' could not be matched to a known table (no table prefix).")

    # 4. Join check (warning) — every JOIN ... ON should reference a real FK relationship
    known_fks = set()
    for t in tables:
        for fk in t.foreign_keys:
            known_fks.add(frozenset({f"{t.table}.{fk.column}".lower(), f"{fk.ref_table}.{fk.ref_column}".lower()}))

    for join in parsed.find_all(exp.Join):
        on = join.args.get("on")
        if on is None:
            continue
        cols = [f"{c.table}.{c.name}".lower() for c in on.find_all(exp.Column) if c.table]
        if len(cols) == 2 and frozenset(cols) not in known_fks:
            report.add("join", "warning",
                       f"Join condition {cols[0]} = {cols[1]} does not match a known foreign-key relationship.")

    # 5. Semantic check (warning) — does SQL structure match the requested intent?
    has_order_by = parsed.find(exp.Order) is not None
    has_limit = parsed.find(exp.Limit) is not None
    if intent.intent == "ranking" and not (has_order_by and has_limit):
        report.add("semantic", "warning",
                   "Intent is 'ranking' but the query has no ORDER BY + LIMIT — "
                   "results may not represent a meaningful top/bottom N.")
    if intent.intent == "trend_analysis" and parsed.find(exp.Group) is None:
        report.add("semantic", "warning",
                   "Intent is 'trend_analysis' but the query has no GROUP BY over a time bucket.")
    if intent.comparison and parsed.find(exp.Group) is None:
        report.add("semantic", "warning",
                   "Intent involves a comparison but the query does not group by the comparison dimension.")

    return report
