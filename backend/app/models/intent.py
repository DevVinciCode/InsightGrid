"""
AnalyticalIntent is the central state object of a conversation. Every
follow-up question modifies an existing AnalyticalIntent rather than
regenerating one from scratch (see conversation/state.py).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

IntentType = Literal[
    "trend_analysis", "comparison", "ranking", "aggregation",
    "distribution", "filtering", "lookup", "unknown",
]

VisualizationHint = Literal[
    "line", "bar", "horizontal_bar", "histogram", "scatter",
    "pie", "waterfall", "table", "unknown",
]


class Filter(BaseModel):
    column: str
    operator: str  # =, !=, IN, >, <, BETWEEN
    value: Any


class AnalyticalIntent(BaseModel):
    intent: IntentType = "unknown"
    metric: str | None = None
    aggregation: str | None = None          # SUM, AVG, COUNT, MIN, MAX
    dimensions: list[str] = Field(default_factory=list)
    time_dimension: str | None = None
    time_granularity: str | None = None     # day, month, quarter, year
    filters: list[Filter] = Field(default_factory=list)
    comparison: dict[str, Any] | None = None
    visualization_hint: VisualizationHint = "unknown"

    def merge(self, update: "AnalyticalIntent") -> "AnalyticalIntent":
        """
        Applies a follow-up intent on top of this one. Only fields the
        follow-up actually specifies are overwritten — this is what lets
        'Only show 2025' modify state instead of resetting it.
        """
        data = self.model_dump()
        update_data = update.model_dump(exclude_defaults=True, exclude_unset=True)
        # merge is applied by the caller via IntentExtractor.extract_followup,
        # which already knows which fields changed; here we just do a shallow
        # dict update to keep this method simple and predictable.
        data.update(update_data)
        return AnalyticalIntent(**data)
