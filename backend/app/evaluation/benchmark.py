"""
Stage 6 evaluation harness. Runs the pipeline (rule-based path) against a
small labeled benchmark and reports the metrics from the design doc
(section 24) that are actually measurable without a human rater in the loop:

  - intent_accuracy          (predicted intent == expected intent)
  - sql_execution_success    (query ran without a DB error)
  - visualization_match      (predicted chart_type == expected)
  - avg_retries, avg_latency_ms

Metrics that genuinely require either an LLM-as-judge or a human rater
(semantic correctness of generated SQL beyond structural checks,
clarification-quality, abstention-quality) are listed but left as
`None` — see docs/evaluation.md for why these need a judge model, and how to
wire one in.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy.engine import Engine

from app.database.executor import execute_safe
from app.database.schema_extractor import extract_schema
from app.intent.extractor import IntentExtractor
from app.rag.retriever import Retriever
from app.services.llm_provider import LLMProvider
from app.sql.generator import SQLGenerator
from app.sql.validator import validate_sql
from app.visualization.planner import plan_visualization

BENCHMARK_QUESTIONS = [
    {"question": "Show monthly revenue by category.", "expected_intent": "trend_analysis",
     "expected_visualization": "line", "answerable": True},
    {"question": "Which product categories generated the most revenue?", "expected_intent": "ranking",
     "expected_visualization": "horizontal_bar", "answerable": True},
    {"question": "Compare Delhi and Mumbai revenue in 2025.", "expected_intent": "comparison",
     "expected_visualization": "bar", "answerable": True},
    {"question": "Show the top 10 products by profit.", "expected_intent": "ranking",
     "expected_visualization": "horizontal_bar", "answerable": True},
    {"question": "What will revenue be next month?", "expected_intent": "unknown",
     "expected_visualization": "table", "answerable": False},
]


@dataclass
class EvalRow:
    question: str
    predicted_intent: str
    expected_intent: str
    intent_match: bool
    sql: str
    sql_ran: bool
    predicted_viz: str
    expected_viz: str
    viz_match: bool
    latency_ms: float


@dataclass
class EvalSummary:
    rows: list[EvalRow] = field(default_factory=list)

    @property
    def intent_accuracy(self) -> float:
        return sum(r.intent_match for r in self.rows) / len(self.rows) if self.rows else 0.0

    @property
    def sql_execution_accuracy(self) -> float:
        return sum(r.sql_ran for r in self.rows) / len(self.rows) if self.rows else 0.0

    @property
    def visualization_match_rate(self) -> float:
        return sum(r.viz_match for r in self.rows) / len(self.rows) if self.rows else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return sum(r.latency_ms for r in self.rows) / len(self.rows) if self.rows else 0.0


def run_benchmark(engine: Engine, provider: LLMProvider) -> EvalSummary:
    retriever = Retriever(engine)
    retriever.build_index()
    intent_extractor = IntentExtractor(provider)
    sql_generator = SQLGenerator(provider)
    tables = extract_schema(engine)

    summary = EvalSummary()
    for case in BENCHMARK_QUESTIONS:
        t0 = time.perf_counter()
        context = retriever.retrieve(case["question"])
        intent = intent_extractor.extract(case["question"], context.as_prompt_block())
        generated = sql_generator.generate(intent, context.as_prompt_block())
        validation = validate_sql(generated.sql, tables, intent)

        sql_ran = False
        viz_type = "table"
        if not validation.has_blocking_errors:
            result = execute_safe(engine, generated.sql)
            sql_ran = result.error is None
            if sql_ran:
                viz_type = plan_visualization(intent, result).chart_type
        latency_ms = (time.perf_counter() - t0) * 1000

        summary.rows.append(EvalRow(
            question=case["question"],
            predicted_intent=intent.intent,
            expected_intent=case["expected_intent"],
            intent_match=(intent.intent == case["expected_intent"]),
            sql=generated.sql,
            sql_ran=sql_ran,
            predicted_viz=viz_type,
            expected_viz=case["expected_visualization"],
            viz_match=(viz_type == case["expected_visualization"]),
            latency_ms=latency_ms,
        ))

    return summary
