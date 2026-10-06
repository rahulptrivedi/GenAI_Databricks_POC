"""Chat request, response, and source citation contracts."""

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

_UC_OBJECT_PATTERN = re.compile(r"^[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*$")


class ExecutionStatus(StrEnum):
    """Public execution states for a chat request."""

    COMPLETE = "complete"
    CLARIFICATION = "clarification"
    NO_DATA = "no_data"
    NOT_CONFIGURED = "not_configured"
    ACCESS_DENIED = "access_denied"
    ERROR = "error"


class ChatRequest(BaseModel):
    """A user question and optional ephemeral Genie conversation identifier."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(min_length=1, max_length=10000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("question")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
            raise ValueError("Question contains unsupported control characters.")
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value


class SourceCitation(BaseModel):
    """A fully qualified Unity Catalog source object."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    object_name: str
    description: str | None = None

    @field_validator("object_name")
    @classmethod
    def require_fully_qualified_name(cls, value: str) -> str:
        if not _UC_OBJECT_PATTERN.fullmatch(value):
            raise ValueError("Source must be a fully qualified catalog.schema.object name.")
        return value


class ChatResponse(BaseModel):
    """Safe, source-attributed response returned to the user interface."""

    answer: str
    status: ExecutionStatus
    correlation_id: str
    conversation_id: str | None = None
    supporting_sql: str | None = None
    sources: list[SourceCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
