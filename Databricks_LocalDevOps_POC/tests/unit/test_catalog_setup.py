import pytest

from scripts.deploy_catalog import bootstrap_statements, grant_statements


def test_bootstrap_sql_is_parseable_idempotent_and_non_destructive() -> None:
    statements = bootstrap_statements("chatbot_demo_dev")
    normalized = [statement.upper() for statement in statements]

    assert len(statements) >= 20
    assert all("CHATBOT_DEMO_DEV" in statement for statement in normalized)
    assert any("MERGE INTO" in statement for statement in normalized)
    assert any("CREATE OR REPLACE VIEW" in statement for statement in normalized)
    assert not any("DROP " in statement for statement in normalized)


@pytest.mark.parametrize(
    "catalog",
    ["main", "chatbot_demo; DROP CATALOG main", "chatbot_demo_prod`;"],
)
def test_bootstrap_rejects_non_demo_or_malformed_catalog_names(catalog: str) -> None:
    with pytest.raises(ValueError, match="chatbot_demo"):
        bootstrap_statements(catalog)


def test_reader_grants_are_limited_to_gold_views() -> None:
    statements = grant_statements("chatbot_demo_test", "analytics-readers@example.com")

    assert len(statements) == 4
    assert all("analytics-readers@example.com" in statement for statement in statements)
    assert any("USE CATALOG" in statement for statement in statements)
    assert any("USE SCHEMA" in statement for statement in statements)
    assert sum("SELECT" in statement for statement in statements) == 2
    assert all("DROP" not in statement for statement in statements)


def test_reader_grants_reject_injected_principal() -> None:
    with pytest.raises(ValueError, match="Principal"):
        grant_statements("chatbot_demo", "readers`; GRANT ALL PRIVILEGES")
