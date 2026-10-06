"""Minimal non-content user feedback contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeedbackRequest(BaseModel):
    """Feedback metadata without prompt, answer, or free-form text."""

    model_config = ConfigDict(extra="forbid")

    correlation_id: str = Field(min_length=36, max_length=36)
    rating: Literal["helpful", "not_helpful"]
