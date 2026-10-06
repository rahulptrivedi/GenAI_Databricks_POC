import os

import pytest

from app.core.config import Settings
from app.models.chat import ExecutionStatus
from app.repositories.genie import DatabricksGenieGateway

pytestmark = pytest.mark.skipif(
    not all(
        os.environ.get(name)
        for name in ("DATABRICKS_HOST", "DATABRICKS_WAREHOUSE_ID", "DATABRICKS_GENIE_AGENT_ID")
    ),
    reason="Requires configured Databricks host, SQL Warehouse, and Genie resource.",
)


def test_genie_answers_from_the_configured_demo_catalog() -> None:
    settings = Settings()
    reply = DatabricksGenieGateway(settings).ask(
        "How many completed orders are represented in the demo data?", None
    )

    assert reply.status is ExecutionStatus.COMPLETE
    assert reply.answer.strip()
    assert reply.sources
    assert all(source.object_name.startswith(f"{settings.catalog}.") for source in reply.sources)
