from app.core.config import Settings
from app.models.chat import ChatRequest, ExecutionStatus, SourceCitation
from app.services.chat_service import ChatService, GenieReply


class FakeGenie:
    def __init__(self, reply: GenieReply | None = None, error: Exception | None = None) -> None:
        self.reply = reply or GenieReply(answer="Revenue was 125.")
        self.error = error
        self.questions: list[tuple[str, str | None]] = []

    def ask(self, question: str, conversation_id: str | None) -> GenieReply:
        self.questions.append((question, conversation_id))
        if self.error:
            raise self.error
        return self.reply


def test_unconfigured_service_does_not_invent_answer() -> None:
    response = ChatService(Settings(), None).answer(ChatRequest(question="Total sales?"))

    assert response.status == ExecutionStatus.NOT_CONFIGURED
    assert "not been configured" in response.answer
    assert response.supporting_sql is None


def test_service_preserves_follow_up_context_and_sources() -> None:
    genie = FakeGenie(
        GenieReply(
            answer="Revenue was 125.",
            conversation_id="conversation-1",
            supporting_sql="select sum(revenue) from chatbot_demo.gold.sales_summary",
            sources=(SourceCitation(object_name="chatbot_demo.gold.sales_summary"),),
        )
    )
    service = ChatService(Settings(DATABRICKS_GENIE_AGENT_ID="space-placeholder"), genie)

    response = service.answer(
        ChatRequest(question="What about last month?", conversation_id="conversation-1")
    )

    assert genie.questions == [("What about last month?", "conversation-1")]
    assert response.conversation_id == "conversation-1"
    assert response.sources[0].object_name == "chatbot_demo.gold.sales_summary"
    assert response.supporting_sql is not None


def test_non_read_only_sql_is_hidden_not_executed() -> None:
    genie = FakeGenie(GenieReply(answer="Done.", supporting_sql="DELETE FROM sales"))
    service = ChatService(Settings(DATABRICKS_GENIE_AGENT_ID="space-placeholder"), genie)

    response = service.answer(ChatRequest(question="Delete sales"))

    assert response.supporting_sql is None
    assert response.warnings
    assert genie.questions == [("Delete sales", None)]


def test_permission_error_is_sanitized() -> None:
    genie = FakeGenie(error=PermissionError("internal table ACL details"))
    service = ChatService(Settings(DATABRICKS_GENIE_AGENT_ID="space-placeholder"), genie)

    response = service.answer(ChatRequest(question="Restricted data?"))

    assert response.status == ExecutionStatus.ACCESS_DENIED
    assert "internal table ACL" not in response.answer
