from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.engine import Engine

from app.api.db_schemas import DatabaseStatusResponse, PostgresConnectRequest, TableSummary
from app.api.schemas import ChatRequest, ChatResponse, DemoQuestionsResponse, SchemaResponse
from app.config.settings import Settings, get_settings
from app.database.manager import ConnectionError_, database_manager
from app.database.schema_extractor import extract_schema
from app.evaluation.benchmark import run_benchmark
from app.services.llm_provider import get_llm_provider
from app.services.pipeline import Pipeline

router = APIRouter()

_pipeline_cache: dict[str, Pipeline] = {}


def _invalidate_pipeline() -> None:
    """Called whenever the active database changes — forces the pipeline
    (and therefore the RAG index, which is built from schema) to rebuild
    against the new engine on the next request."""
    _pipeline_cache.pop("pipeline", None)


database_manager.on_change(_invalidate_pipeline)


def get_engine() -> Engine:
    return database_manager.engine


def get_pipeline(settings: Settings = Depends(get_settings), engine: Engine = Depends(get_engine)) -> Pipeline:
    if "pipeline" not in _pipeline_cache:
        provider = get_llm_provider(settings)
        _pipeline_cache["pipeline"] = Pipeline(engine, provider, settings)
    return _pipeline_cache["pipeline"]


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, pipeline: Pipeline = Depends(get_pipeline)) -> ChatResponse:
    try:
        result = pipeline.run_turn(req.session_id, req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(**result)


@router.get("/schema", response_model=SchemaResponse)
def get_schema(engine: Engine = Depends(get_engine)) -> SchemaResponse:
    tables = extract_schema(engine)
    return SchemaResponse(tables=[
        {
            "table": t.table,
            "row_count": t.row_count,
            "description": t.description,
            "columns": [
                {"name": c.name, "type": c.type, "primary_key": c.primary_key,
                 "nullable": c.nullable, "sample_values": c.sample_values}
                for c in t.columns
            ],
            "foreign_keys": [
                {"column": fk.column, "ref_table": fk.ref_table, "ref_column": fk.ref_column}
                for fk in t.foreign_keys
            ],
        }
        for t in tables
    ])


def _build_status_response(engine: Engine) -> DatabaseStatusResponse:
    tables = extract_schema(engine)
    summaries = [
        TableSummary(
            name=t.table,
            row_count=t.row_count,
            column_count=len(t.columns),
            columns=[c.name for c in t.columns],
        )
        for t in tables
    ]
    total = sum(t.row_count for t in tables)
    return DatabaseStatusResponse(
        kind=database_manager.info.kind,
        label=database_manager.info.label,
        tables=[t.table for t in tables],
        table_summaries=summaries,
        total_rows=total,
    )


def _generate_suggested_questions(tables: list) -> tuple[list[str], list[str]]:
    questions = []
    ambiguous = []
    for t in tables:
        t_name = t.table
        col_names = [c.name.lower() for c in t.columns]
        num_cols = [c.name for c in t.columns if any(w in c.type.upper() for w in ("INT", "NUM", "FLOAT", "REAL", "DEC", "DOUBLE"))]
        text_cols = [c.name for c in t.columns if any(w in c.type.upper() for w in ("CHAR", "TEXT", "STR", "VARCHAR")) or c.name.lower() in ("name", "city", "status", "category", "segment", "type")]

        if num_cols and text_cols:
            questions.append(f"Show top 10 {t_name} by {num_cols[0]}.")
            questions.append(f"What is the total {num_cols[0]} grouped by {text_cols[0]} in {t_name}?")
        elif text_cols:
            questions.append(f"Count records in {t_name} grouped by {text_cols[0]}.")
        else:
            questions.append(f"Show the first 10 records from {t_name}.")

        ambiguous.append(f"Which {t_name} are performing best?")

    if not questions:
        questions = ["Show the top 10 rows from the database."]
    return questions[:6], ambiguous[:4]


@router.get("/demo-questions", response_model=DemoQuestionsResponse)
def demo_questions(engine: Engine = Depends(get_engine)) -> DemoQuestionsResponse:
    if database_manager.info.kind == "demo":
        return DemoQuestionsResponse(
            questions=[
                "What was our monthly revenue last year?",
                "Which product categories generated the most revenue?",
                "Which customers generated the highest revenue?",
                "Compare Delhi and Mumbai revenue in 2025.",
                "Show the top 10 products by profit.",
                "Show revenue by month and category.",
            ],
            ambiguous_examples=[
                "Which customers are most valuable?",
                "Which products are performing poorly?",
                "What will revenue be next month?",
                "Show our best region.",
            ],
        )

    # Dynamic suggestions for uploaded/custom dataset
    tables = extract_schema(engine)
    q_list, amb_list = _generate_suggested_questions(tables)
    return DemoQuestionsResponse(questions=q_list, ambiguous_examples=amb_list)


@router.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    from app.conversation.state import conversation_store
    conversation_store.reset(session_id)
    return {"status": "reset", "session_id": session_id}


@router.get("/evaluation/run")
def evaluation_run(settings: Settings = Depends(get_settings), engine: Engine = Depends(get_engine)):
    provider = get_llm_provider(settings)
    summary = run_benchmark(engine, provider)
    return {
        "intent_accuracy": summary.intent_accuracy,
        "sql_execution_accuracy": summary.sql_execution_accuracy,
        "visualization_match_rate": summary.visualization_match_rate,
        "avg_latency_ms": summary.avg_latency_ms,
        "rows": [r.__dict__ for r in summary.rows],
        "note": "Structural metrics only. Semantic-correctness / clarification-quality / "
                "abstention-quality metrics need an LLM-judge or human rater — see docs/evaluation.md.",
    }


# ---------------------------------------------------------------------------
# Database connection management (design doc section 4)
# ---------------------------------------------------------------------------

@router.get("/database/status", response_model=DatabaseStatusResponse)
def database_status(engine: Engine = Depends(get_engine)) -> DatabaseStatusResponse:
    return _build_status_response(engine)


@router.post("/database/use-demo", response_model=DatabaseStatusResponse)
def use_demo_database() -> DatabaseStatusResponse:
    database_manager.use_demo()
    return _build_status_response(database_manager.engine)


@router.post("/database/upload-sqlite", response_model=DatabaseStatusResponse)
async def upload_sqlite(file: UploadFile = File(...)) -> DatabaseStatusResponse:
    fname = file.filename.lower()
    if not (fname.endswith((".db", ".sqlite", ".sqlite3", ".csv"))):
        raise HTTPException(status_code=400, detail="Please upload a .db, .sqlite, .sqlite3, or .csv file.")
    content = await file.read()
    try:
        database_manager.use_file_upload(content, file.filename)
    except ConnectionError_ as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _build_status_response(database_manager.engine)


@router.post("/database/connect-postgres", response_model=DatabaseStatusResponse)
def connect_postgres(req: PostgresConnectRequest) -> DatabaseStatusResponse:
    try:
        database_manager.use_postgres(req.host, req.port, req.database, req.user, req.password)
    except ConnectionError_ as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _build_status_response(database_manager.engine)


@router.get("/table/{table_name}/preview")
def get_table_preview(table_name: str, limit: int = 25, engine: Engine = Depends(get_engine)):
    tables = extract_schema(engine)
    match = next((t for t in tables if t.table.lower() == table_name.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found.")

    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT * FROM "{match.table}" LIMIT :limit'), {"limit": limit})
        cols = list(result.keys())
        raw_rows = result.fetchall()
        rows = [[str(val) if val is not None else None for val in r] for r in raw_rows]

    return {
        "table": match.table,
        "columns": cols,
        "rows": rows,
        "row_count": match.row_count,
        "description": match.description,
        "column_details": [
            {
                "name": c.name,
                "type": c.type,
                "primary_key": c.primary_key,
                "nullable": c.nullable,
                "sample_values": c.sample_values,
            }
            for c in match.columns
        ],
    }

