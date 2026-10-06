"""Read-only SQL validation for SQL returned for display only."""

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class SqlValidation:
    """Result of validating a single read-only SQL statement."""

    is_read_only: bool
    normalized_sql: str | None = None
    reason: str | None = None


def validate_read_only_sql(sql: str) -> SqlValidation:
    """Accept one SELECT-like statement; this function never executes SQL."""
    if not sql.strip():
        return SqlValidation(False, reason="SQL is empty.")

    try:
        statements = sqlglot.parse(sql, read="databricks")
    except ParseError:
        return SqlValidation(False, reason="SQL could not be parsed safely.")

    if len(statements) != 1 or statements[0] is None:
        return SqlValidation(False, reason="Only one SQL statement can be displayed.")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        return SqlValidation(False, reason="Only read-only query statements can be displayed.")

    forbidden_nodes = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Command)
    if any(isinstance(node, forbidden_nodes) for node in statement.walk()):
        return SqlValidation(False, reason="SQL contains a disallowed operation.")

    return SqlValidation(True, normalized_sql=statement.sql(dialect="databricks"))
