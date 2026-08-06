from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FarmContext(StrictModel):
    county: str | None = Field(default=None, max_length=100)
    operation_type: Literal["confinement", "open_feedlot", "mixed", "unknown"] = "unknown"
    animal_unit_capacity: int | None = Field(default=None, ge=1, le=1_000_000)
    manure_storage: Literal["formed", "unformed", "lagoon", "dry", "unknown"] = "unknown"
    workers: Literal["family", "nonfamily", "both", "unknown"] = "unknown"
    sells_into_california: Literal["yes", "no", "unknown"] = "unknown"


class ChatRequest(StrictModel):
    question: str = Field(min_length=3, max_length=2000)
    conversation_id: str | None = None
    source_tiers: list[int] = Field(default_factory=lambda: [1, 2])
    topics: list[str] = Field(default_factory=list)
    farm_context: FarmContext | None = None

    @field_validator("source_tiers")
    @classmethod
    def valid_tiers(cls, value: list[int]) -> list[int]:
        cleaned = sorted(set(value))
        if not cleaned or any(tier not in (1, 2, 3) for tier in cleaned):
            raise ValueError("source_tiers must include one or more of 1, 2, or 3")
        return cleaned


class CitedClaim(StrictModel):
    text: str = Field(min_length=1, max_length=1000)
    citations: list[str] = Field(default_factory=list, max_length=6)


class Applicability(StrictModel):
    level: Literal["high", "medium", "low", "unknown"]
    explanation: str = Field(min_length=1, max_length=600)


class GeneratedAnswer(StrictModel):
    short_answer: list[CitedClaim] = Field(min_length=1, max_length=4)
    why: list[CitedClaim] = Field(default_factory=list, max_length=6)
    rules: list[CitedClaim] = Field(default_factory=list, max_length=8)
    documentation: list[CitedClaim] = Field(default_factory=list, max_length=8)
    related_questions: list[str] = Field(default_factory=list, max_length=4)
    applicability: Applicability
    evidence_status: Literal["verified", "insufficient", "conflicting"]
    missing_facts: list[str] = Field(default_factory=list, max_length=6)
    limitations: list[str] = Field(default_factory=list, max_length=6)


class Citation(StrictModel):
    id: str
    title: str
    agency: str
    url: HttpUrl
    effective_date: str | None = None
    publication_date: str | None = None
    retrieved_at: datetime
    excerpt: str


class ChatResponse(GeneratedAnswer):
    id: str
    conversation_id: str
    citations: list[Citation]
    created_at: datetime


class FeedbackRequest(StrictModel):
    answer_id: str
    rating: Literal["helpful", "not_helpful"]
    comment: str | None = Field(default=None, max_length=2000)


class BookmarkRequest(StrictModel):
    answer_id: str


class SavedResponse(StrictModel):
    id: str
    saved: bool = True


class SourceResponse(StrictModel):
    id: str
    title: str
    agency: str
    url: HttpUrl
    topic: str
    source_tier: int
    jurisdiction: str
    status: str
    publication_date: str | None
    effective_date: str | None
    retrieved_at: datetime


class SourceUpdateResponse(StrictModel):
    document_id: str
    title: str
    agency: str
    url: HttpUrl
    version_count: int
    latest_retrieved_at: datetime
    previous_retrieved_at: datetime


class ConversationMessageResponse(StrictModel):
    role: Literal["user", "assistant"]
    content: dict
    created_at: datetime


class ConversationResponse(StrictModel):
    id: str
    messages: list[ConversationMessageResponse]
