from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.intent import AnalyticalIntent


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ConfidenceReport(BaseModel):
    note: str = "Heuristic system-confidence scores, not calibrated probabilities."
    intent_confidence: float
    schema_confidence: float
    join_confidence: float
    sql_confidence: float
    result_confidence: float


class Provenance(BaseModel):
    question: str
    intent: AnalyticalIntent
    retrieved_documents: list[dict[str, Any]]
    sql: str
    reasoning_summary: str
    filters_applied: list[dict[str, Any]]


class ChatResponse(BaseModel):
    session_id: str
    answer_status: str  # answered | error | blocked
    intent: AnalyticalIntent
    sql: str
    reasoning_summary: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    validation_issues: list[dict[str, str]]
    verification_flags: list[str]
    visualization: dict[str, Any]
    confidence: ConfidenceReport
    provenance: Provenance
    retry_log: list[str] = []


class SchemaResponse(BaseModel):
    tables: list[dict[str, Any]]


class DemoQuestionsResponse(BaseModel):
    questions: list[str]
    ambiguous_examples: list[str]
