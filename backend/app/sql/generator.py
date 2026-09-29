"""
Generates SQL from: question + analytical intent + retrieved schema context.

Two paths, same output contract ({"sql", "reasoning_summary", "tables_used",
"columns_used"}):
  - LLM path: prompts the configured provider with intent + retrieved context.
  - Template path (default, no API key): builds SQL directly from the
    AnalyticalIntent against the known demo schema. This is intentionally a
    template engine, not a general NL-to-SQL model — it exists so the MVP is
    demoable with zero configuration, per the "clone and run" requirement.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.intent import AnalyticalIntent
from app.services.llm_provider import LLMProvider, RuleBasedProvider, try_parse_json

METRIC_COLUMN = {
    "revenue": "orders.revenue",
    "profit": "orders.profit",
    "units_sold": "orders.quantity",
    "order_count": "orders.order_id",
}

DIMENSION_COLUMN = {
    "category": ("products", "products.category"),
    "city": ("customers", "customers.city"),
    "state": ("customers", "customers.state"),
    "segment": ("customers", "customers.segment"),
    "product_name": ("products", "products.product_name"),
}

BASE_JOIN = (
    "FROM orders "
    "JOIN customers ON orders.customer_id = customers.customer_id "
    "JOIN products ON orders.product_id = products.product_id"
)

SYSTEM_PROMPT = """You are a senior database architect and analytics expert writing read-only SQL queries.
Rules:
1. Output ONLY a valid JSON object:
{"sql": "SELECT ...", "reasoning_summary": "...", "tables_used": [...], "columns_used": [...]}
2. The "sql" field must be an executable, read-only SELECT or WITH statement using real tables and columns from the schema context.
3. For trend/time-series questions (e.g. "plot monthly revenue over time", "sales trend"), group by date/month (e.g. strftime('%Y-%m', date_col) AS month or period) and ORDER BY month.
4. For multi-table analytics (e.g. revenue when order_items has quantity & unit_price, and orders has order_date), JOIN tables and compute SUM(quantity * unit_price).
5. For comparisons between periods (e.g. "between May and June 2025"), filter using WHERE date >= '...' AND date <= '...' and GROUP BY month/period.
6. For rankings/top N, ORDER BY metric DESC LIMIT 10.
7. For distributions, GROUP BY the category/dimension and calculate COUNT(*) or SUM.
8. Return ONLY the JSON object. No conversational prose outside the JSON."""


def clean_sql(raw_sql: str) -> str:
    import re
    if not raw_sql:
        return ""
    s = raw_sql.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:sql)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()
    if not re.match(r"^\s*(WITH|SELECT)\b", s, re.IGNORECASE):
        match = re.search(r"\b(WITH|SELECT)\b[\s\S]+?(?:;|$)", s, re.IGNORECASE)
        if match:
            s = match.group(0).strip()
    return s.rstrip(";")


@dataclass
class GeneratedSQL:
    sql: str
    reasoning_summary: str
    tables_used: list[str]
    columns_used: list[str]


def _agg_expr(intent: AnalyticalIntent) -> str:
    col = METRIC_COLUMN.get(intent.metric or "revenue", "orders.revenue")
    agg = intent.aggregation or "SUM"
    if intent.metric == "order_count":
        return "COUNT(orders.order_id)"
    return f"{agg}({col})"


def _template_generate(intent: AnalyticalIntent) -> GeneratedSQL:
    metric_expr = _agg_expr(intent)
    metric_alias = intent.metric or "revenue"
    tables_used = {"orders"}
    columns_used = {METRIC_COLUMN.get(intent.metric or "revenue", "orders.revenue")}

    select_parts = []
    group_by_parts = []

    if intent.time_dimension and intent.time_granularity:
        if intent.time_granularity == "month":
            time_expr = "strftime('%Y-%m', orders.order_date)"
        elif intent.time_granularity == "year":
            time_expr = "strftime('%Y', orders.order_date)"
        else:
            time_expr = "orders.order_date"
        select_parts.append(f"{time_expr} AS period")
        group_by_parts.append(time_expr)
        columns_used.add("orders.order_date")

    for dim in intent.dimensions:
        table, col = DIMENSION_COLUMN.get(dim, (None, None))
        if col:
            select_parts.append(f"{col} AS {dim}")
            group_by_parts.append(col)
            columns_used.add(col)
            if table:
                tables_used.add(table)

    select_parts.append(f"{metric_expr} AS {metric_alias}")

    where_clauses = ["orders.status = 'completed'"]
    for f in intent.filters:
        if f.column == "year":
            where_clauses.append(f"strftime('%Y', orders.order_date) = '{f.value}'")
        elif f.column in ("city", "state", "segment"):
            _, col = DIMENSION_COLUMN[f.column]
            tables_used.add("customers")
            if f.operator == "IN" and isinstance(f.value, list):
                vals = ", ".join(f"'{v}'" for v in f.value)
                where_clauses.append(f"{col} IN ({vals})")
            else:
                where_clauses.append(f"{col} = '{f.value}'")

    sql = f"SELECT {', '.join(select_parts)}\n{BASE_JOIN}\nWHERE {' AND '.join(where_clauses)}"
    if group_by_parts:
        sql += f"\nGROUP BY {', '.join(group_by_parts)}"
        # Order results sensibly: chronological if time-based, else descending metric
        if intent.time_dimension:
            sql += f"\nORDER BY {group_by_parts[0]}"
        else:
            sql += f"\nORDER BY {metric_alias} DESC"
    else:
        pass  # single-value aggregate, no GROUP BY needed

    if intent.intent == "ranking":
        sql += f"\nORDER BY {metric_alias} DESC" if "ORDER BY" not in sql else ""
        sql += "\nLIMIT 10"

    reasoning = f"Aggregates {metric_alias} from orders"
    if intent.dimensions:
        reasoning += f", grouped by {', '.join(intent.dimensions)}"
    if intent.time_dimension:
        reasoning += f", trended by {intent.time_granularity or 'time'}"
    reasoning += ", restricted to completed orders."

    return GeneratedSQL(
        sql=sql,
        reasoning_summary=reasoning,
        tables_used=sorted(tables_used),
        columns_used=sorted(columns_used),
    )


class SQLGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate(self, intent: AnalyticalIntent, retrieved_context_text: str = "") -> GeneratedSQL:
        if isinstance(self._provider, RuleBasedProvider):
            return _template_generate(intent)

        user_prompt = (
            f"Analytical intent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"Retrieved schema/business context:\n{retrieved_context_text}"
        )
        raw = self._provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
        parsed = try_parse_json(raw)
        if parsed is None or "sql" not in parsed:
            return _template_generate(intent)
        cleaned = clean_sql(parsed.get("sql", ""))
        return GeneratedSQL(
            sql=cleaned,
            reasoning_summary=parsed.get("reasoning_summary", ""),
            tables_used=parsed.get("tables_used", []),
            columns_used=parsed.get("columns_used", []),
        )

    def regenerate_after_error(
        self, intent: AnalyticalIntent, failed_sql: str, db_error: str, retrieved_context_text: str = ""
    ) -> GeneratedSQL:
        """Stage-2 error-feedback loop: give the LLM the failed SQL + error and ask for a fix."""
        if isinstance(self._provider, RuleBasedProvider):
            # Template generator is deterministic and schema-validated by construction,
            # so there's nothing to "retry" — surface the error as-is.
            return _template_generate(intent)

        user_prompt = (
            f"The previous SQL failed.\nSQL:\n{failed_sql}\n\nDatabase error:\n{db_error}\n\n"
            f"Analytical intent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"Retrieved schema/business context:\n{retrieved_context_text}\n\n"
            f"Return corrected JSON in the same format."
        )
        raw = self._provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
        parsed = try_parse_json(raw)
        if parsed is None or "sql" not in parsed:
            return _template_generate(intent)
        cleaned = clean_sql(parsed.get("sql", ""))
        return GeneratedSQL(
            sql=cleaned,
            reasoning_summary=parsed.get("reasoning_summary", ""),
            tables_used=parsed.get("tables_used", []),
            columns_used=parsed.get("columns_used", []),
        )
