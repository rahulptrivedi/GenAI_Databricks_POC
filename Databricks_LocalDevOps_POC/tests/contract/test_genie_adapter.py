from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.repositories.genie import DatabricksGenieGateway


class FakeGenieSdk:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    def start_conversation(self, **kwargs: str) -> SimpleNamespace:
        self.calls.append(("start_conversation", kwargs))
        return SimpleNamespace(conversation_id="conversation-1", message_id="message-1")

    def create_message(self, **kwargs: str) -> SimpleNamespace:
        self.calls.append(("create_message", kwargs))
        return SimpleNamespace(message_id="message-2")

    def get_message(self, **kwargs: str) -> object:
        self.calls.append(("get_message", kwargs))
        return self.response


class FakeWorkspace:
    def __init__(self, genie: FakeGenieSdk) -> None:
        self.genie = genie


def test_adapter_maps_answer_sql_and_allowlisted_source() -> None:
    response = SimpleNamespace(
        status="COMPLETED",
        attachments=[
            SimpleNamespace(text=SimpleNamespace(content="Revenue was 125."), query=None),
            SimpleNamespace(
                text=None,
                query=SimpleNamespace(
                    query="SELECT sum(revenue) FROM chatbot_demo.gold.sales_summary"
                ),
            ),
        ],
    )
    sdk = FakeGenieSdk(response)
    gateway = DatabricksGenieGateway(Settings(DATABRICKS_GENIE_AGENT_ID="test-space"))
    gateway._client = FakeWorkspace(sdk)

    reply = gateway.ask("What was revenue?", None)

    assert reply.answer == "Revenue was 125."
    assert reply.conversation_id == "conversation-1"
    assert reply.supporting_sql is not None
    assert [source.object_name for source in reply.sources] == ["chatbot_demo.gold.sales_summary"]
    assert sdk.calls[0][0] == "start_conversation"
    assert sdk.calls[0][1]["space_id"] == "test-space"


def test_adapter_continues_existing_conversation() -> None:
    response = SimpleNamespace(status="COMPLETED", attachments=[])
    sdk = FakeGenieSdk(response)
    gateway = DatabricksGenieGateway(Settings(DATABRICKS_GENIE_AGENT_ID="test-space"))
    gateway._client = FakeWorkspace(sdk)

    reply = gateway.ask("And the month before?", "conversation-1")

    assert reply.conversation_id == "conversation-1"
    assert sdk.calls[0] == (
        "create_message",
        {
            "space_id": "test-space",
            "conversation_id": "conversation-1",
            "content": "And the month before?",
        },
    )


def test_pending_genie_response_has_a_finite_poll_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(status="RUNNING", attachments=[])
    sdk = FakeGenieSdk(response)
    gateway = DatabricksGenieGateway(
        Settings(
            DATABRICKS_GENIE_AGENT_ID="test-space",
            GENIE_TIMEOUT_SECONDS=1,
            GENIE_POLL_INTERVAL_SECONDS=30,
        )
    )
    gateway._client = FakeWorkspace(sdk)
    sleeps: list[float] = []
    monkeypatch.setattr("app.repositories.genie.time.sleep", sleeps.append)
    monkeypatch.setattr("app.repositories.genie.time.monotonic", lambda: 0.0)

    with pytest.raises(TimeoutError, match="timed out"):
        gateway._wait_for_message(FakeWorkspace(sdk), "conversation-1", "message-1")

    assert len(sdk.calls) == 2
    assert sleeps == [1.0]
