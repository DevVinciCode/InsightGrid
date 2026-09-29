import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.config.settings import Settings
from app.database.connection import build_engine
from app.database.schema_extractor import extract_schema
from app.models.intent import AnalyticalIntent
from app.sql.validator import validate_sql


def get_tables():
    settings = Settings(DB_TYPE="sqlite")
    engine = build_engine(settings)
    return extract_schema(engine)


def test_ranking_without_order_by_warns():
    tables = get_tables()
    sql = "SELECT product_name, SUM(revenue) as revenue FROM orders JOIN products ON orders.product_id = products.product_id GROUP BY product_name LIMIT 5"
    report = validate_sql(sql, tables, AnalyticalIntent(intent="ranking", metric="revenue"))
    assert any(i.level == "semantic" for i in report.issues)


def test_nonexistent_table_is_schema_error():
    tables = get_tables()
    sql = "SELECT * FROM nonexistent_table"
    report = validate_sql(sql, tables, AnalyticalIntent())
    assert any(i.level == "schema" and i.severity == "error" for i in report.issues)
    assert report.has_blocking_errors


def test_write_statement_is_blocked():
    tables = get_tables()
    sql = "DELETE FROM orders WHERE 1=1"
    report = validate_sql(sql, tables, AnalyticalIntent())
    assert report.has_blocking_errors
    assert any(i.level == "safety" for i in report.issues)


def test_clean_select_passes():
    tables = get_tables()
    sql = "SELECT category, SUM(revenue) as revenue FROM orders JOIN products ON orders.product_id = products.product_id GROUP BY category ORDER BY revenue DESC"
    report = validate_sql(sql, tables, AnalyticalIntent(intent="aggregation"))
    assert not report.has_blocking_errors


if __name__ == "__main__":
    test_ranking_without_order_by_warns()
    test_nonexistent_table_is_schema_error()
    test_write_statement_is_blocked()
    test_clean_select_passes()
    print("All validator tests passed.")
