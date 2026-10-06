"""Databricks SDK adapter for Genie conversations."""

import logging
import math
import time
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.config import Settings
from app.models.chat import ExecutionStatus, SourceCitation
from app.services.chat_service import GenieReply
from app.services.sql_safety import validate_read_only_sql

logger = logging.getLogger(__name__)


class DatabricksGenieGateway:
    """Call the configured Genie resource through the Databricks SDK."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any | None = None

    def ask(self, question: str, conversation_id: str | None) -> GenieReply:
        """Start or continue a Genie conversation and await its response."""
        client = self._workspace_client()
        try:
            if conversation_id:
                started = client.genie.create_message(
                    space_id=self._settings.genie_agent_id,
                    conversation_id=conversation_id,
                    content=question,
                )
                active_conversation_id = conversation_id
            else:
                started = client.genie.start_conversation(
                    space_id=self._settings.genie_agent_id,
                    content=question,
                )
                active_conversation_id = started.conversation_id
        except Exception as error:
            self._raise_sanitized_platform_error(error)
            raise

        message = self._wait_for_message(
            client,
            active_conversation_id,
            started.message_id,
        )
        return self._map_message(message, active_conversation_id)

    def _workspace_client(self) -> Any:
        if self._client is None:
            from databricks.sdk import WorkspaceClient
            from databricks.sdk.config import Config

            request_timeout = min(
                self._settings.genie_timeout_seconds,
                self._settings.genie_http_timeout_seconds,
            )
            self._client = WorkspaceClient(
                config=Config(
                    http_timeout_seconds=request_timeout,
                    retry_timeout_seconds=request_timeout,
                )
            )
        return self._client

    def _wait_for_message(self, client: Any, conversation_id: str, message_id: str) -> Any:
        timeout = self._settings.genie_timeout_seconds
        poll_interval = min(self._settings.genie_poll_interval_seconds, timeout)
        max_polls = math.ceil(timeout / poll_interval) + 1
        deadline = time.monotonic() + timeout
        for poll_index in range(max_polls):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                message = client.genie.get_message(
                    space_id=self._settings.genie_agent_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                )
            except Exception as error:
                self._raise_sanitized_platform_error(error)
                raise

            message_status = self._status_name(message.status)
            if message_status in {"completed", "failed", "cancelled", "canceled"}:
                return message
            remaining = deadline - time.monotonic()
            if remaining <= 0 or poll_index == max_polls - 1:
                break
            time.sleep(min(poll_interval, remaining))
        raise TimeoutError("Genie response timed out.")

    def _map_message(self, message: Any, conversation_id: str) -> GenieReply:
        message_status = self._status_name(message.status)
        if message_status != "completed":
            return GenieReply(
                answer="The data service could not complete this request.",
                conversation_id=conversation_id,
                status=ExecutionStatus.ERROR,
                warning="Genie did not complete the request.",
            )

        answer_parts: list[str] = []
        sql_candidates: list[str] = []
        for attachment in message.attachments or []:
            text_content = getattr(getattr(attachment, "text", None), "content", None)
            if isinstance(text_content, str) and text_content.strip():
                answer_parts.append(text_content.strip())

            query_text = getattr(getattr(attachment, "query", None), "query", None)
            if isinstance(query_text, str) and query_text.strip():
                sql_candidates.append(query_text)

        sql = next(
            (
                candidate
                for candidate in sql_candidates
                if validate_read_only_sql(candidate).is_read_only
            ),
            None,
        )
        sources = self._sources_from_sql(sql) if sql else ()
        return GenieReply(
            answer="\n\n".join(answer_parts),
            conversation_id=conversation_id,
            supporting_sql=sql,
            sources=sources,
            status=ExecutionStatus.COMPLETE,
        )

    def _sources_from_sql(self, sql: str) -> tuple[SourceCitation, ...]:
        try:
            query = sqlglot.parse_one(sql, read="databricks")
        except ParseError:
            return ()

        sources: dict[str, SourceCitation] = {}
        for table in query.find_all(exp.Table):
            if table.catalog and table.db:
                catalog, schema, name = table.catalog, table.db, table.name
            elif table.db:
                catalog, schema, name = self._settings.catalog, table.db, table.name
            else:
                catalog, schema, name = (
                    self._settings.catalog,
                    self._settings.schema_name,
                    table.name,
                )
            if catalog != self._settings.catalog or schema != self._settings.schema_name:
                continue
            full_name = f"{catalog}.{schema}.{name}"
            try:
                sources[full_name] = SourceCitation(object_name=full_name)
            except ValueError:
                logger.warning("genie_source_omitted reason=invalid_object_name")
        return tuple(sources.values())

    @staticmethod
    def _status_name(value: Any) -> str:
        return str(getattr(value, "value", value)).rsplit(".", maxsplit=1)[-1].lower()

    @staticmethod
    def _raise_sanitized_platform_error(error: Exception) -> None:
        if type(error).__name__ in {"PermissionDenied", "Unauthenticated", "Unauthorized"}:
            raise PermissionError("Genie access denied.") from error
