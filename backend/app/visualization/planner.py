"""
Maps analytical intent + result shape to a visualization spec. Deliberately
NOT "ask an LLM to choose a chart" — the mapping is a fixed, explainable
table (see design doc section 14), which also lets the planner double as a
verification step (section 15): if the result shape doesn't fit the intended
chart, that's a signal of a possible SQL/semantic error.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.database.executor import ExecutionResult
from app.models.intent import AnalyticalIntent

INTENT_TO_CHART = {
    "trend_analysis": "line",
    "comparison": "bar",
    "ranking": "horizontal_bar",
    "distribution": "histogram",
    "aggregation": "bar",
    "filtering": "table",
    "lookup": "table",
    "unknown": "table",
}


@dataclass
class VisualizationSpec:
    chart_type: str
    x: str | None
    y: str | None
    group: str | None
    title: str
    filters: list[dict] = field(default_factory=list)
    structure_mismatch: str | None = None  # set if result shape doesn't fit the chart


def _is_numeric(val: Any) -> bool:
    if val is None:
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def plan_visualization(intent: AnalyticalIntent, result: ExecutionResult) -> VisualizationSpec:
    chart_type = intent.visualization_hint if intent.visualization_hint != "unknown" \
        else INTENT_TO_CHART.get(intent.intent, "table")

    columns = result.columns
    if not columns:
        return VisualizationSpec(chart_type="table", x=None, y=None, group=None, title="Result", filters=[])

    # Smart column classification
    time_keywords = ("date", "month", "year", "period", "day", "time", "week", "quarter")
    metric_keywords = ("revenue", "sales", "profit", "count", "quantity", "price", "amount", "total", "avg", "sum", "units")

    # Sample the first row to check actual data types
    first_row = result.rows[0] if result.rows else []
    col_is_num = {}
    for i, col in enumerate(columns):
        val = first_row[i] if i < len(first_row) else None
        col_is_num[col] = _is_numeric(val)

    # Detect x_col (dimension or time)
    x_col = None
    # 1. Prefer time columns
    for col in columns:
        if any(kw in col.lower() for kw in time_keywords):
            x_col = col
            if chart_type in ("table", "unknown"):
                chart_type = "line"
            break

    # 2. Prefer intent dimensions
    if not x_col and intent.dimensions:
        for dim in intent.dimensions:
            if dim in columns:
                x_col = dim
                break

    # 3. Prefer non-numeric columns
    if not x_col:
        for col in columns:
            if not col_is_num.get(col, False):
                x_col = col
                break

    # 4. Fallback to first column if there are at least 2 columns
    if not x_col and len(columns) > 1:
        x_col = columns[0]

    # Detect y_col (metric)
    y_col = None
    # 1. Check metric keywords in numeric columns
    for col in columns:
        if col != x_col and any(kw in col.lower() for kw in metric_keywords):
            y_col = col
            break

    # 2. First numeric column that isn't x_col
    if not y_col:
        for col in columns:
            if col != x_col and col_is_num.get(col, False):
                y_col = col
                break

    # 3. Fallback to last column
    if not y_col and len(columns) > 1:
        y_col = columns[-1] if columns[-1] != x_col else columns[0]

    # Group col for multi-dimensional breakdowns
    group_col = None
    if len(columns) >= 3:
        for col in columns:
            if col not in (x_col, y_col) and not col_is_num.get(col, False):
                group_col = col
                break

    # If chart_type is still table, but we have an x and numeric y with rows > 1, default to bar or line
    if chart_type in ("table", "unknown") and x_col and y_col and result.row_count > 1:
        if any(kw in x_col.lower() for kw in time_keywords):
            chart_type = "line"
        elif result.row_count <= 8:
            chart_type = "bar"
        else:
            chart_type = "horizontal_bar"

    title_parts = []
    if y_col:
        title_parts.append(y_col.replace("_", " ").title())
    elif intent.metric:
        title_parts.append(intent.metric.replace("_", " ").title())
    if x_col:
        title_parts.append("by " + x_col.replace("_", " ").title())
    elif intent.dimensions:
        title_parts.append("by " + ", ".join(intent.dimensions))
    if group_col:
        title_parts.append(f"and {group_col.replace('_', ' ').title()}")
    title = " ".join(title_parts) or "Query Visualization"

    mismatch = None
    if chart_type in ("line", "area") and result.row_count < 2:
        # If only 1 data point, bar chart works better than line
        chart_type = "bar"

    filters_out = [{"column": f.column, "operator": f.operator, "value": f.value} for f in intent.filters]

    return VisualizationSpec(
        chart_type=chart_type,
        x=x_col,
        y=y_col,
        group=group_col,
        title=title,
        filters=filters_out,
        structure_mismatch=mismatch,
    )
