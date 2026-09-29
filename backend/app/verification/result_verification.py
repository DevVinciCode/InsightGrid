"""
Inspects an executed result and flags structural mismatches against the
analytical intent — e.g. a trend_analysis question that returned one row
instead of one row per time bucket.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.database.executor import ExecutionResult
from app.models.intent import AnalyticalIntent


@dataclass
class VerificationReport:
    flags: list[str] = field(default_factory=list)
    passed: bool = True

    def add(self, message: str) -> None:
        self.flags.append(message)
        self.passed = False


def verify_result(result: ExecutionResult, intent: AnalyticalIntent) -> VerificationReport:
    report = VerificationReport()

    if result.error:
        report.add(f"Execution error: {result.error}")
        return report

    if result.row_count == 0:
        report.add("Query returned zero rows — possible over-restrictive filter or empty period.")
        return report

    expected_min_cols = 1  # metric
    if intent.dimensions:
        expected_min_cols += len(intent.dimensions)
    if intent.time_dimension:
        expected_min_cols += 1

    if len(result.columns) < expected_min_cols:
        report.add(
            f"Expected at least {expected_min_cols} column(s) "
            f"(metric + {len(intent.dimensions)} dimension(s) + "
            f"{'1 time bucket' if intent.time_dimension else '0 time buckets'}), "
            f"got {len(result.columns)}. Possible semantic mismatch between SQL and intent."
        )

    if intent.intent == "trend_analysis" and result.row_count == 1:
        report.add(
            "Intent is 'trend_analysis' (expects a value per time period) but the result "
            "has a single aggregated row — the SQL may be missing its GROUP BY."
        )

    if intent.comparison and result.row_count < 2:
        report.add("Intent is a comparison but fewer than 2 rows were returned.")

    for row in result.rows[:50]:
        if all(v is None for v in row):
            report.add("At least one row is entirely NULL — check join/filter correctness.")
            break

    return report
