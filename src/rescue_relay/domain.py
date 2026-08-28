"""Typed domain contracts shared by the agent, API, and deterministic engine."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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
    id: str
    donor: str
    category: FoodCategory
    pounds: int = Field(gt=0)
    description: str
    pickup_date: date
    pickup_start: str
    pickup_end: str
    requires_confirmation: bool = False
    source_text: str
    received_at: datetime


class Pantry(BaseModel):
    id: str
    name: str
    needs: dict[FoodCategory, int]
    capacity: dict[FoodCategory, int]
    distance_miles: float = Field(ge=0)
    available_start: str
    available_end: str


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
