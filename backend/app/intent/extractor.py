"""
Converts a natural-language question (+ retrieved RAG context + prior state)
into a structured AnalyticalIntent.

Two paths:
  - LLM path: prompts the configured provider for structured JSON.
  - Rule-based path (default, no API key): simple keyword/pattern matching.
    Deliberately simple — good enough to demo the pipeline end-to-end, and
    clearly a fallback rather than a claimed research contribution.
"""
from __future__ import annotations

import re

from app.models.intent import AnalyticalIntent, Filter
from app.services.llm_provider import LLMProvider, RuleBasedProvider, try_parse_json

METRIC_KEYWORDS = {
    "revenue": ["revenue", "sales", "income"],
    "profit": ["profit", "margin"],
    "units_sold": ["units", "quantity sold", "items sold"],
    "order_count": ["orders", "number of orders", "order count"],
}

DIMENSION_KEYWORDS = {
    "category": ["category", "categories"],
    "city": ["city", "cities"],
    "state": ["state", "states"],
    "segment": ["segment"],
    "product_name": ["product"],
}

CHART_BY_INTENT = {
    "trend_analysis": "line",
    "comparison": "bar",
    "ranking": "horizontal_bar",
    "distribution": "histogram",
    "aggregation": "bar",
    "filtering": "table",
    "lookup": "table",
}

SYSTEM_PROMPT = """You convert a natural-language analytics question into a strict JSON object
matching this schema:
{
  "intent": "trend_analysis|comparison|ranking|aggregation|distribution|filtering|lookup|unknown",
  "metric": "<a column name or short metric label from the retrieved schema/business context below, or null>",
  "aggregation": "SUM|AVG|COUNT|MIN|MAX|null",
  "dimensions": ["<column name(s) from the retrieved schema to group/break down by>", ...],
  "time_dimension": "<a date/time column name from the retrieved schema, or null>",
  "time_granularity": "day|month|quarter|year|null",
  "filters": [{"column": "<column name from the retrieved schema>", "operator": "=|!=|IN|>|<|BETWEEN", "value": ...}],
  "comparison": null or {"type": "period_over_period", "values": [...]},
  "visualization_hint": "line|bar|horizontal_bar|histogram|scatter|pie|waterfall|table|unknown"
}
IMPORTANT: "metric", "dimensions", "time_dimension", and filter "column" values must be real
column names that appear in the retrieved schema/business context you are given below — do not
invent columns, and do not assume any particular domain (the connected database could be
e-commerce, healthcare, logs, finance, or anything else). If the context doesn't contain a
column that matches what the question is asking for, leave the field null/empty rather than
guessing a name from a different domain.
Return ONLY the JSON object, no prose, no markdown fences."""


def _rule_based_extract(question: str, retrieved_context_text: str = "") -> AnalyticalIntent:
    q = question.lower()

    metric = None
    for m, kws in METRIC_KEYWORDS.items():
        if any(kw in q for kw in kws):
            metric = m
            break

    dimensions = []
    for dim, kws in DIMENSION_KEYWORDS.items():
        if any(kw in q for kw in kws):
            dimensions.append(dim)

    filters: list[Filter] = []
    year_match = re.search(r"\b(20\d{2})\b", q)
    years = re.findall(r"\b20\d{2}\b", q)

    comparison = None
    intent: str = "unknown"

    if "compare" in q or " vs " in q or "versus" in q:
        intent = "comparison"
        if len(years) >= 2:
            comparison = {"type": "period_over_period", "values": years}
    elif any(w in q for w in ["top", "best", "highest", "worst", "lowest", "ranking"]):
        intent = "ranking"
    elif any(w in q for w in ["trend", "over time", "monthly", "by month", "each month", "growth"]):
        intent = "trend_analysis"
    elif any(w in q for w in ["distribution", "spread", "breakdown"]):
        intent = "distribution"
    elif metric or dimensions:
        intent = "aggregation"

    if year_match and not comparison:
        filters.append(Filter(column="year", operator="=", value=int(year_match.group(1))))

    time_granularity = "month" if "month" in q else ("year" if "year" in q and intent == "trend_analysis" else None)
    time_dimension = "order_date" if (intent == "trend_analysis" or time_granularity) else None

    aggregation = "COUNT" if metric == "order_count" else ("SUM" if metric else None)

    viz = CHART_BY_INTENT.get(intent, "table")

    return AnalyticalIntent(
        intent=intent,  # type: ignore[arg-type]
        metric=metric,
        aggregation=aggregation,
        dimensions=dimensions,
        time_dimension=time_dimension,
        time_granularity=time_granularity,
        filters=filters,
        comparison=comparison,
        visualization_hint=viz,  # type: ignore[arg-type]
    )


class IntentExtractor:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def extract(self, question: str, retrieved_context_text: str = "") -> AnalyticalIntent:
        if isinstance(self._provider, RuleBasedProvider):
            return _rule_based_extract(question, retrieved_context_text)

        user_prompt = f"Retrieved schema/business context:\n{retrieved_context_text}\n\nQuestion: {question}"
        raw = self._provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
        parsed = try_parse_json(raw)
        if parsed is None:
            # LLM misbehaved — fall back rather than crash the pipeline.
            return _rule_based_extract(question, retrieved_context_text)
        try:
            return AnalyticalIntent(**parsed)
        except Exception:
            return _rule_based_extract(question, retrieved_context_text)

    def extract_followup(self, question: str, prior: AnalyticalIntent, retrieved_context_text: str = "") -> AnalyticalIntent:
        """
        Extracts only what the follow-up changes, then merges onto prior state.
        Rule-based version: re-extracts and merges non-empty fields over prior.
        """
        new_partial = self.extract(question, retrieved_context_text)
        merged = prior.model_copy(deep=True)

        if new_partial.metric:
            merged.metric = new_partial.metric
        if new_partial.aggregation:
            merged.aggregation = new_partial.aggregation
        if new_partial.dimensions:
            merged.dimensions = new_partial.dimensions
        if new_partial.time_dimension:
            merged.time_dimension = new_partial.time_dimension
        if new_partial.time_granularity:
            merged.time_granularity = new_partial.time_granularity
        if new_partial.filters:
            # "Only 2025" should replace a prior year filter, not stack with it
            merged.filters = [f for f in merged.filters if f.column != "year"] + \
                              [f for f in new_partial.filters]
        if new_partial.comparison:
            merged.comparison = new_partial.comparison
            merged.intent = "comparison"
        elif new_partial.intent != "unknown":
            merged.intent = new_partial.intent
        if new_partial.visualization_hint != "unknown":
            merged.visualization_hint = new_partial.visualization_hint

        return merged
