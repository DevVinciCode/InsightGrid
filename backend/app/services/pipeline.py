"""
Orchestrates one conversational turn end-to-end:

  question -> RAG retrieval -> intent (new or follow-up merge)
  -> SQL generation -> multi-level validation -> safe execution
  -> (retry loop on DB error, up to MAX_SQL_RETRIES) -> result verification
  -> visualization planning -> confidence scoring -> provenance assembly
  -> conversation state update

This is Stage 1+2 of the design doc, fully wired. Stage 3 (uncertainty-gated
clarification/probing) is implemented in intent/clarification.py and
verification/probing.py but NOT called from here yet — see docs/architecture.md
for the wiring plan; flipping it on is a small, well-scoped follow-up change,
deliberately not rushed into this pass.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from app.config.settings import Settings
from app.conversation.state import ConversationSession, Turn, conversation_store
from app.database.executor import execute_safe
from app.database.schema_extractor import extract_schema
from app.intent.extractor import IntentExtractor
from app.rag.retriever import Retriever
from app.services.llm_provider import LLMProvider, RuleBasedProvider
from app.sql.generator import SQLGenerator
from app.sql.validator import validate_sql
from app.verification.result_verification import verify_result
from app.verification.uncertainty import (
    intent_confidence, join_confidence, result_confidence, schema_confidence, sql_confidence,
)
from app.visualization.planner import plan_visualization


class Pipeline:
    def __init__(self, engine: Engine, provider: LLMProvider, settings: Settings) -> None:
        self._engine = engine
        self._settings = settings
        self._provider = provider
        self._retriever = Retriever(engine, settings.VECTOR_STORE)
        self._retriever.build_index()
        self._intent_extractor = IntentExtractor(provider)
        self._sql_generator = SQLGenerator(provider)

    def run_turn(self, session_id: str, question: str) -> dict:
        from app.database.manager import database_manager

        session: ConversationSession = conversation_store.get_or_create(session_id)
        tables = extract_schema(self._engine)

        # If on rule-based provider, check if the current database contains tables compatible with the template engine
        table_names = {t.table.lower() for t in tables}
        has_compatible_tables = "orders" in table_names and ("customers" in table_names or "products" in table_names)
        if isinstance(self._provider, RuleBasedProvider) and database_manager.info.kind != "demo" and not has_compatible_tables:
            return {
                "session_id": session_id, "answer_status": "blocked",
                "intent": self._intent_extractor.extract(question),
                "sql": "", "reasoning_summary": "",
                "columns": [], "rows": [], "row_count": 0, "truncated": False,
                "validation_issues": [{
                    "level": "config", "severity": "error",
                    "message": (
                        "You've connected a custom database, but LLM_PROVIDER is still "
                        "'rulebased' — that mode only understands the bundled demo schema. "
                        "Set LLM_PROVIDER=groq (or openai/gemini) and LLM_API_KEY in backend/.env "
                        "and restart the backend to ask questions against this custom database."
                    ),
                }],
                "verification_flags": [],
                "visualization": {"chart_type": "table", "x": None, "y": None, "group": None, "title": "", "filters": []},
                "confidence": {
                    "intent_confidence": 0.0, "schema_confidence": 0.0, "join_confidence": 0.0,
                    "sql_confidence": 0.0, "result_confidence": 0.0,
                },
                "provenance": {
                    "question": question, "intent": {}, "retrieved_documents": [],
                    "sql": "", "reasoning_summary": "", "filters_applied": [],
                },
                "retry_log": [],
            }

        context = self._retriever.retrieve(question, top_k=self._settings.RAG_TOP_K)
        context_text = context.as_prompt_block()

        prior_intent = session.current_intent
        if prior_intent is not None:
            intent = self._intent_extractor.extract_followup(question, prior_intent, context_text)
        else:
            intent = self._intent_extractor.extract(question, context_text)

        generated = self._sql_generator.generate(intent, context_text)
        validation = validate_sql(generated.sql, tables, intent)

        retry_log: list[str] = []
        result = None
        sql_used = generated.sql

        if not validation.has_blocking_errors:
            result = execute_safe(
                self._engine, sql_used,
                row_limit=self._settings.SQL_ROW_LIMIT,
                timeout_seconds=self._settings.SQL_TIMEOUT_SECONDS,
            )
            attempt = 1
            while result.error and attempt <= self._settings.MAX_SQL_RETRIES:
                retry_log.append(f"Attempt {attempt} failed: {result.error}")
                corrected = self._sql_generator.regenerate_after_error(
                    intent, sql_used, result.error, context_text
                )
                sql_used = corrected.sql
                generated = corrected
                validation = validate_sql(sql_used, tables, intent)
                if validation.has_blocking_errors:
                    break
                result = execute_safe(
                    self._engine, sql_used,
                    row_limit=self._settings.SQL_ROW_LIMIT,
                    timeout_seconds=self._settings.SQL_TIMEOUT_SECONDS,
                )
                attempt += 1
            if result.error is None and retry_log:
                retry_log.append(f"Attempt {attempt} succeeded.")

        answer_status = "answered"
        verification_flags: list[str] = []
        viz_spec = {"chart_type": "table", "x": None, "y": None, "group": None, "title": "", "filters": []}
        r_confidence = 0.0

        if validation.has_blocking_errors:
            answer_status = "blocked"
        elif result is None or result.error:
            answer_status = "error"
        else:
            verification = verify_result(result, intent)
            verification_flags = verification.flags
            viz = plan_visualization(intent, result)
            viz_spec = {
                "chart_type": viz.chart_type, "x": viz.x, "y": viz.y, "group": viz.group,
                "title": viz.title, "filters": viz.filters, "structure_mismatch": viz.structure_mismatch,
            }
            r_confidence = result_confidence(verification.passed)

            session.add_turn(Turn(question=question, intent=intent, sql=sql_used, chart_type=viz.chart_type))

        confidence = {
            "intent_confidence": intent_confidence(intent),
            "schema_confidence": schema_confidence(validation),
            "join_confidence": join_confidence(validation),
            "sql_confidence": sql_confidence(validation),
            "result_confidence": r_confidence,
        }

        provenance = {
            "question": question,
            "intent": intent.model_dump(),
            "retrieved_documents": [
                {"kind": d.kind, "text": d.text, "score": s}
                for d, s in zip(context.documents, context.scores)
            ],
            "sql": sql_used,
            "reasoning_summary": generated.reasoning_summary,
            "filters_applied": [f.model_dump() for f in intent.filters],
        }

        return {
            "session_id": session_id,
            "answer_status": answer_status,
            "intent": intent,
            "sql": sql_used,
            "reasoning_summary": generated.reasoning_summary,
            "columns": result.columns if result else [],
            "rows": result.rows if result else [],
            "row_count": result.row_count if result else 0,
            "truncated": result.truncated if result else False,
            "validation_issues": [
                {"level": i.level, "severity": i.severity, "message": i.message}
                for i in validation.issues
            ],
            "verification_flags": verification_flags,
            "visualization": viz_spec,
            "confidence": confidence,
            "provenance": provenance,
            "retry_log": retry_log,
        }
