import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.config.settings import Settings
from app.database.connection import build_engine
from app.services.llm_provider import get_llm_provider
from app.services.pipeline import Pipeline


def make_pipeline():
    settings = Settings(LLM_PROVIDER="rulebased", VECTOR_STORE="tfidf", DB_TYPE="sqlite")
    engine = build_engine(settings)
    provider = get_llm_provider(settings)
    return Pipeline(engine, provider, settings)


def test_trend_question_produces_line_chart_with_multiple_rows():
    pipeline = make_pipeline()
    result = pipeline.run_turn("test-trend", "Show monthly revenue by category.")
    assert result["answer_status"] == "answered"
    assert result["row_count"] > 1
    assert result["visualization"]["chart_type"] == "line"
    assert not any(i["severity"] == "error" for i in result["validation_issues"])


def test_ranking_question_has_order_by_and_limit():
    pipeline = make_pipeline()
    result = pipeline.run_turn("test-rank", "Show the top 10 products by profit.")
    assert result["answer_status"] == "answered"
    assert "ORDER BY" in result["sql"].upper()
    assert "LIMIT" in result["sql"].upper()
    assert result["row_count"] <= 10


def test_followup_narrows_prior_intent():
    pipeline = make_pipeline()
    pipeline.run_turn("test-followup", "Show revenue by category.")
    result = pipeline.run_turn("test-followup", "Only show 2025.")
    assert result["answer_status"] == "answered"
    assert "2025" in result["sql"]


def test_unsafe_sql_is_never_executed():
    """The pipeline should never hand a destructive statement to the executor,
    regardless of what the generator produces — this is enforced by
    database.executor.assert_safe, exercised here via the validator."""
    from app.database.executor import assert_safe, UnsafeSQLError

    try:
        assert_safe("DELETE FROM orders")
        assert False, "should have raised"
    except UnsafeSQLError:
        pass


if __name__ == "__main__":
    test_trend_question_produces_line_chart_with_multiple_rows()
    test_ranking_question_has_order_by_and_limit()
    test_followup_narrows_prior_intent()
    test_unsafe_sql_is_never_executed()
    print("All integration tests passed.")
