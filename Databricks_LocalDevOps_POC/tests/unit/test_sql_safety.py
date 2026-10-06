import pytest

from app.services.sql_safety import validate_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT count(*) FROM chatbot_demo.gold.sales_summary",
        "WITH monthly AS (SELECT month, revenue FROM sales) SELECT * FROM monthly",
    ],
)
def test_accepts_read_only_queries(sql: str) -> None:
    result = validate_read_only_sql(sql)

    assert result.is_read_only
    assert result.normalized_sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM sales",
        "SELECT 1; DROP TABLE sales",
        "CREATE TABLE x AS SELECT 1",
        "UPDATE sales SET amount = 0",
    ],
)
def test_rejects_mutating_or_multiple_statements(sql: str) -> None:
    assert not validate_read_only_sql(sql).is_read_only


def test_rejects_unparseable_sql() -> None:
    assert not validate_read_only_sql("SELECT FROM").is_read_only
