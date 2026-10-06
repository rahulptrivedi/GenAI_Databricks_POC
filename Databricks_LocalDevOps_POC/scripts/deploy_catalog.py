"""Deploy the synthetic Unity Catalog demo objects through the SQL Statement API."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot.errors import ParseError

from app.core.config import Settings

LOGGER = logging.getLogger("catalog_setup")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SQL = PROJECT_ROOT / "resources" / "sql" / "bootstrap.sql"
DEMO_CATALOG_PATTERN = re.compile(r"chatbot_demo(?:_[a-z][a-z0-9_]*)?\Z")
PRINCIPAL_PATTERN = re.compile(r"[A-Za-z0-9_.@-]+\Z")


def bootstrap_statements(catalog: str) -> list[str]:
    """Return parsed demo setup statements with a validated catalog identifier."""
    if not DEMO_CATALOG_PATTERN.fullmatch(catalog):
        raise ValueError(
            "DATABRICKS_CATALOG must be chatbot_demo or a chatbot_demo_<environment> name."
        )
    source = BOOTSTRAP_SQL.read_text(encoding="utf-8").replace("__CATALOG__", catalog)
    try:
        parsed = sqlglot.parse(source, read="databricks")
    except ParseError as error:
        raise ValueError("The catalog bootstrap SQL could not be parsed.") from error
    return [statement.sql(dialect="databricks") for statement in parsed if statement is not None]


def grant_statements(catalog: str, principal: str) -> list[str]:
    """Return least-privilege gold-view grants for one validated UC principal."""
    if not DEMO_CATALOG_PATTERN.fullmatch(catalog):
        raise ValueError(
            "DATABRICKS_CATALOG must be chatbot_demo or a chatbot_demo_<environment> name."
        )
    if not PRINCIPAL_PATTERN.fullmatch(principal):
        raise ValueError(
            "Principal must contain only letters, numbers, underscore, dot, @, or hyphen."
        )
    grant_path = PROJECT_ROOT / "resources" / "sql" / "grants" / "gold_reader.sql"
    source = grant_path.read_text(encoding="utf-8")
    source = source.replace("__CATALOG__", catalog).replace("__PRINCIPAL__", principal)
    try:
        parsed = sqlglot.parse(source, read="databricks")
    except ParseError as error:
        raise ValueError("The gold-reader grants could not be parsed.") from error
    return [statement.sql(dialect="databricks") for statement in parsed if statement is not None]


def execute_statements(settings: Settings, statements: list[str]) -> None:
    """Execute setup statements in order using the configured warehouse."""
    if not settings.warehouse_id:
        raise ValueError("Set DATABRICKS_WAREHOUSE_ID before deploying catalog objects.")

    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient()
    for index, statement in enumerate(statements, start=1):
        response: Any = client.statement_execution.execute_statement(
            warehouse_id=settings.warehouse_id,
            statement=statement,
            wait_timeout="50s",
        )
        state = getattr(getattr(response, "status", None), "state", None)
        state_name = str(getattr(state, "value", state)).upper()
        if state_name != "SUCCEEDED":
            raise RuntimeError(
                f"Catalog statement {index} did not succeed (status={state_name or 'unknown'})."
            )
        LOGGER.info("catalog_statement_succeeded index=%d total=%d", index, len(statements))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser(
        "seed", help="Create or refresh synthetic demo objects; does not delete data."
    )
    grant_parser = actions.add_parser(
        "grant-reader", help="Grant read-only access to the two curated gold views."
    )
    grant_parser.add_argument(
        "--principal", required=True, help="Exact UC user or group principal."
    )
    clean_parser = actions.add_parser(
        "clean", help="Drop only the explicitly confirmed demo catalog."
    )
    clean_parser.add_argument(
        "--confirm-catalog",
        required=True,
        help="Type the exact chatbot_demo catalog name.",
    )
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        settings = Settings()
        if arguments.action == "seed":
            statements = bootstrap_statements(settings.catalog)
        elif arguments.action == "grant-reader":
            statements = grant_statements(settings.catalog, arguments.principal)
        else:
            if arguments.confirm_catalog != settings.catalog:
                raise ValueError("Confirmation must exactly match DATABRICKS_CATALOG.")
            if not DEMO_CATALOG_PATTERN.fullmatch(settings.catalog):
                raise ValueError("Cleanup is restricted to chatbot_demo catalogs.")
            if not settings.warehouse_id:
                raise ValueError("Set DATABRICKS_WAREHOUSE_ID before cleanup.")
            statements = [f"DROP CATALOG IF EXISTS `{settings.catalog}` CASCADE"]
        execute_statements(settings, statements)
    except Exception as error:
        LOGGER.error(
            "catalog_operation_failed error_type=%s message=%s",
            type(error).__name__,
            error,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
