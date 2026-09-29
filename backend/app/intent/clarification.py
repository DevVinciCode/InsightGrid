"""
STAGE 3 SCAFFOLD — NOT YET WIRED INTO THE MAIN PIPELINE.

Design for the ANSWER / INVESTIGATE / ASK / ABSTAIN decision described in the
research doc (section 9). Left as a scaffold rather than faked: a real
implementation needs (a) an ambiguity taxonomy grounded in the actual schema,
and (b) a policy for when investigation (Stage-3 database probing, see
verification/probing.py) can resolve ambiguity without asking the user.

Wiring plan (see docs/architecture.md "Stage 3"):
  1. After IntentExtractor.extract(), call `decide(question, intent, schema)`.
  2. If decision == ASK, return the generated question to the user instead of
     proceeding to SQL generation.
  3. If decision == INVESTIGATE, run a bounded probe (see probing.py stub)
     and re-run the decision with the extra evidence.
  4. If decision == ABSTAIN, return a message explaining why the system can't
     safely answer (e.g. "next month's revenue" — no forecasting capability).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.database.schema_extractor import TableMeta
from app.models.intent import AnalyticalIntent

AMBIGUOUS_TERMS = {
    "best": ["revenue", "profit", "order_count"],
    "top": ["revenue", "profit", "units_sold"],
    "worst": ["revenue", "profit"],
    "performing poorly": ["revenue", "profit", "units_sold"],
    "valuable": ["revenue", "profit"],
}

UNANSWERABLE_PATTERNS = ["next month", "next year", "will be", "forecast", "predict"]


class Decision(str, Enum):
    ANSWER = "ANSWER"
    INVESTIGATE = "INVESTIGATE"
    ASK = "ASK"
    ABSTAIN = "ABSTAIN"


@dataclass
class ClarificationResult:
    decision: Decision
    question_to_user: str | None = None
    reason: str = ""


def decide(question: str, intent: AnalyticalIntent, tables: list[TableMeta]) -> ClarificationResult:
    q = question.lower()

    if any(p in q for p in UNANSWERABLE_PATTERNS):
        return ClarificationResult(
            decision=Decision.ABSTAIN,
            reason="Question asks for a future/predictive value; this system only answers "
                   "questions about historical data in the connected database.",
        )

    for term, candidate_metrics in AMBIGUOUS_TERMS.items():
        if term in q and not intent.metric:
            options = ", ".join(candidate_metrics)
            return ClarificationResult(
                decision=Decision.ASK,
                question_to_user=f"Which metric should define '{term}': {options}?",
                reason=f"Ambiguous term '{term}' with no metric specified in the question.",
            )

    return ClarificationResult(decision=Decision.ANSWER, reason="No ambiguity detected.")
