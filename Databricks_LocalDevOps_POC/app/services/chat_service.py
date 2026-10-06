"""Orchestrate a grounded Genie request without executing returned SQL."""

import logging
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.core.config import Settings
from app.models.chat import ChatRequest, ChatResponse, ExecutionStatus, SourceCitation
from app.services.sql_safety import validate_read_only_sql

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenieReply:
    """Platform-neutral result returned by the Genie adapter."""

    answer: str
    conversation_id: str | None = None
    supporting_sql: str | None = None
    sources: tuple[SourceCitation, ...] = ()
    status: ExecutionStatus = ExecutionStatus.COMPLETE
    warning: str | None = None


class GenieGateway(Protocol):
    """Structural interface implemented by a Databricks Genie adapter."""

    def ask(self, question: str, conversation_id: str | None) -> GenieReply:
        """Ask Genie and return a normalized response."""


class ChatService:
    """Validate, orchestrate, and safely map one chat request."""

    def __init__(self, settings: Settings, genie: GenieGateway | None) -> None:
        self._settings = settings
        self._genie = genie

    def answer(self, request: ChatRequest) -> ChatResponse:
        """Return a safe user-facing response with a correlation identifier."""
        correlation_id = str(uuid4())
        if len(request.question) > self._settings.question_max_chars:
            return ChatResponse(
                answer=f"Please keep questions to {self._settings.question_max_chars} characters.",
                status=ExecutionStatus.ERROR,
                correlation_id=correlation_id,
            )

        if not self._settings.genie_configured or self._genie is None:
            return ChatResponse(
                answer="A Genie resource has not been configured for this environment.",
                status=ExecutionStatus.NOT_CONFIGURED,
                correlation_id=correlation_id,
            )

        try:
            reply = self._genie.ask(request.question, request.conversation_id)
        except PermissionError:
            logger.warning("Genie authorization denied correlation_id=%s", correlation_id)
            return ChatResponse(
                answer="You do not have access to the data required for this question.",
                status=ExecutionStatus.ACCESS_DENIED,
                correlation_id=correlation_id,
            )
        except Exception as error:
            logger.error(
                "Genie request failed correlation_id=%s error_type=%s",
                correlation_id,
                type(error).__name__,
            )
            return ChatResponse(
                answer=(
                    "The data service could not complete this request. "
                    "Share the request ID with support."
                ),
                status=ExecutionStatus.ERROR,
                correlation_id=correlation_id,
            )

        warnings = [reply.warning] if reply.warning else []
        supporting_sql = None
        if reply.supporting_sql:
            sql_result = validate_read_only_sql(reply.supporting_sql)
            if sql_result.is_read_only:
                supporting_sql = sql_result.normalized_sql
            else:
                warnings.append(
                    "Supporting SQL was hidden because it did not pass the read-only check."
                )

        answer = reply.answer.strip() or "No matching data was found for this question."
        status = reply.status
        if not reply.answer.strip() and status == ExecutionStatus.COMPLETE:
            status = ExecutionStatus.NO_DATA

        return ChatResponse(
            answer=answer,
            status=status,
            correlation_id=correlation_id,
            conversation_id=reply.conversation_id,
            supporting_sql=supporting_sql,
            sources=list(reply.sources),
            warnings=warnings,
        )
