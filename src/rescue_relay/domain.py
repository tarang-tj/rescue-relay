"""Typed domain contracts shared by the agent, API, and deterministic engine."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class FoodCategory(StrEnum):
    PRODUCE = "produce"
    BAKERY = "bakery"
    DAIRY = "dairy"
    SHELF_STABLE = "shelf_stable"


class DispatchState(StrEnum):
    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    SCHEDULED = "scheduled"
    DECLINED = "declined"
    MESSAGE_SENT = "message_sent"


class DecisionState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class IntakeEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Offer(BaseModel):
    id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]+$")
    donor: str = Field(min_length=1, max_length=200)
    category: FoodCategory
    pounds: int = Field(gt=0, le=100_000)
    description: str = Field(min_length=1, max_length=500)
    pickup_date: date
    pickup_start: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    pickup_end: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    requires_confirmation: bool = False
    source_text: str = Field(min_length=1, max_length=5_000)
    received_at: datetime

    @model_validator(mode="after")
    def validate_pickup_window(self):
        if self.pickup_start >= self.pickup_end:
            raise ValueError("pickup_start must be before pickup_end")
        return self


class Pantry(BaseModel):
    id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]+$")
    name: str = Field(min_length=1, max_length=200)
    needs: dict[FoodCategory, int]
    capacity: dict[FoodCategory, int]
    distance_miles: float = Field(ge=0, le=10_000)
    available_start: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    available_end: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @model_validator(mode="after")
    def validate_constraints(self):
        if self.available_start >= self.available_end:
            raise ValueError("available_start must be before available_end")
        if any(value < 0 or value > 100_000 for value in (*self.needs.values(), *self.capacity.values())):
            raise ValueError("needs and capacity values must be between 0 and 100000")
        return self


class Allocation(BaseModel):
    pantry_id: str
    pantry_name: str
    pounds: int
    reason: str


class Dispatch(BaseModel):
    id: str
    offer_id: str
    donor: str
    description: str
    pounds: int
    offered_pounds: int = 0
    unallocated_pounds: int = 0
    allocations: list[Allocation]
    pickup_date: date | None = None
    pickup_window: str
    confidence: int = Field(ge=0, le=100)
    state: DispatchState
    decision_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class Decision(BaseModel):
    id: str
    kind: str
    title: str
    context: str
    dispatch_id: str
    state: DecisionState = DecisionState.PENDING
    created_at: datetime
    resolved_at: datetime | None = None
    resolution_note: str | None = None


class MessageDraft(BaseModel):
    id: str
    dispatch_id: str
    recipient: str
    subject: str
    body: str
    state: str = "staged"
    created_at: datetime


class Evidence(BaseModel):
    id: str
    kind: str
    label: str
    detail: str
    captured_at: datetime


class RunStep(BaseModel):
    id: str
    tool: str
    label: str
    detail: str
    status: str = "complete"
    started_at: datetime
    duration_ms: int = 0
    evidence_ids: list[str] = Field(default_factory=list)


class AgentRun(BaseModel):
    id: str
    mode: str
    model_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    summary: str = ""
    steps: list[RunStep] = Field(default_factory=list)
    error: str | None = None


class IntakeEvent(BaseModel):
    id: str
    source: str
    mode: str
    status: IntakeEventStatus = IntakeEventStatus.RECEIVED
    received_at: datetime
    completed_at: datetime | None = None
    run_id: str | None = None
    error: str | None = None
    payload_sha256: str = ""
    offer_count: int = 0
    partner_count: int = 0


class EventPayload(BaseModel):
    """Validated normalized inputs stored internally for durable event processing."""

    offers: list[Offer] = Field(min_length=1, max_length=50)
    partners: list[Pantry] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        offer_ids = [item.id for item in self.offers]
        partner_ids = [item.id for item in self.partners]
        if len(offer_ids) != len(set(offer_ids)):
            raise ValueError("offer IDs must be unique within an event")
        if len(partner_ids) != len(set(partner_ids)):
            raise ValueError("partner IDs must be unique within an event")
        return self


class Impact(BaseModel):
    pounds_matched: int
    meals_estimated: int
    minutes_saved: int


class Dashboard(BaseModel):
    active_run: AgentRun | None
    dispatches: list[Dispatch]
    decisions: list[Decision]
    message_drafts: list[MessageDraft] = Field(default_factory=list)
    evidence: list[Evidence]
    impact: Impact
    run_history: list[AgentRun] = Field(default_factory=list)
    intake_events: list[IntakeEvent] = Field(default_factory=list)
