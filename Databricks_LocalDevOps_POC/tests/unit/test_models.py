import pytest
from pydantic import ValidationError

from app.models.chat import ChatRequest, SourceCitation


def test_request_rejects_blank_question() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(question="  ")


def test_request_rejects_control_characters() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(question="show\x00secret")


def test_citation_requires_fully_qualified_uc_name() -> None:
    with pytest.raises(ValidationError):
        SourceCitation(object_name="sales")
