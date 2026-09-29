"""
Heuristic confidence scores for each pipeline stage.

IMPORTANT: these are simple heuristic system-confidence scores, NOT
statistically calibrated probabilities. They are useful as relative signals
("this query is shakier than that one") and are labelled as such everywhere
they're surfaced to the user (see api/schemas.py: ConfidenceReport).

Calibrating these against real accuracy is listed as future work in
docs/research_direction.md — do not treat these numbers as ground truth.
"""
from __future__ import annotations

from app.models.intent import AnalyticalIntent
from app.sql.validator import ValidationReport


def intent_confidence(intent: AnalyticalIntent) -> float:
    score = 0.5
    if intent.intent != "unknown":
        score += 0.2
    if intent.metric:
        score += 0.15
    if intent.dimensions or intent.time_dimension:
        score += 0.1
    if intent.filters:
        score += 0.05
    return round(min(score, 0.99), 2)


def schema_confidence(validation: ValidationReport) -> float:
    schema_errors = [i for i in validation.issues if i.level == "schema" and i.severity == "error"]
    schema_warnings = [i for i in validation.issues if i.level == "schema" and i.severity == "warning"]
    if schema_errors:
        return 0.2
    if schema_warnings:
        return 0.7
    return 0.97


def join_confidence(validation: ValidationReport) -> float:
    join_warnings = [i for i in validation.issues if i.level == "join"]
    return 0.6 if join_warnings else 0.95


def sql_confidence(validation: ValidationReport) -> float:
    errors = [i for i in validation.issues if i.severity == "error"]
    warnings = [i for i in validation.issues if i.severity == "warning"]
    if errors:
        return 0.15
    if warnings:
        return 0.65
    return 0.95


def result_confidence(verification_passed: bool) -> float:
    return 0.95 if verification_passed else 0.4
