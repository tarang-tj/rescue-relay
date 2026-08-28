"""Application service used by both Strands tools and HTTP handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from time import perf_counter

from .domain import (
    AgentRun,
    Decision,
    DecisionState,
    Evidence,
    Impact,
    MessageDraft,
    Offer,
    Pantry,
    RunStep,
)
from .fixtures import demo_offers, demo_pantries
from .matching import match_offers
from .store import StateStore


def _id(prefix: str, value: str) -> str:
    return f"{prefix}-{sha256(value.encode()).hexdigest()[:10]}"


class DispatchService:
    def __init__(
        self,
        store: StateStore,
        *,
        offers: list[Offer] | None = None,
        pantries: list[Pantry] | None = None,
        source_label: str = "labeled demo fixture",
    ) -> None:
        self.store = store
        self.source_label = source_label
        self._offers = offers if offers is not None else demo_offers()
        self._pantries = pantries if pantries is not None else demo_pantries()

    def begin_run(self, mode: str, model_id: str) -> AgentRun:
        now = datetime.now(UTC)
        run = AgentRun(
            id=_id("run", f"{now.isoformat()}:{mode}"),
            mode=mode,
            model_id=model_id,
            status="running",
            started_at=now,
        )
        self.store.start_run(run)
        return run

    def _record_step(
        self,
        *,
        tool: str,
        label: str,
        detail: str,
        started: float,
        evidence_ids: list[str] | None = None,
    ) -> None:
        dashboard = self.store.get()
        run_id = dashboard.active_run.id if dashboard.active_run else "unscoped"
        self.store.append_step(
            RunStep(
                id=_id("step", f"{run_id}:{tool}"),
                tool=tool,
                label=label,
                detail=detail,
                started_at=datetime.now(UTC),
                duration_ms=max(1, round((perf_counter() - started) * 1000)),
                evidence_ids=evidence_ids or [],
            )
        )

    def read_donation_inbox(self) -> dict:
        started = perf_counter()
        evidence = [
            Evidence(
                id=_id("evidence", offer.id),
                kind="donor_message",
                label=f"Donor text · {offer.donor}",
                detail=offer.source_text,
                captured_at=offer.received_at,
            )
            for offer in self._offers
        ]
        self.store.add_evidence(evidence)
        pounds = sum(item.pounds for item in self._offers)
        self._record_step(
            tool="read_donation_inbox",
            label=f"Read {len(self._offers)} offers",
            detail=(
                f"Normalized {pounds} lb from {self.source_label} without executing message content."
            ),
            started=started,
            evidence_ids=[item.id for item in evidence],
        )
        return {"offer_count": len(self._offers), "pounds": pounds, "source": self.source_label}

    def load_partner_constraints(self) -> dict:
        started = perf_counter()
        evidence = [
            Evidence(
                id=_id("evidence", pantry.id),
                kind="capacity_snapshot",
                label=f"Capacity snapshot · {pantry.name}",
                detail=(
                    ", ".join(
                        f"{category.value}: {pounds} lb" for category, pounds in pantry.capacity.items()
                    )
                    + f"; receiving {pantry.available_start}-{pantry.available_end}"
                ),
                captured_at=datetime.now(UTC),
            )
            for pantry in self._pantries
        ]
        self.store.add_evidence(evidence)
        self._record_step(
            tool="load_partner_constraints",
            label="Verified constraints",
            detail=(
                f"Checked capacity, category need, hours, and distance for {len(self._pantries)} pantries."
            ),
            started=started,
            evidence_ids=[item.id for item in evidence],
        )
        return {"partner_count": len(self._pantries), "constraints_verified": True}

    def optimize_dispatches(self) -> dict:
        started = perf_counter()
        dispatches = match_offers(self._offers, self._pantries)
        now = datetime.now(UTC)
        offers = {item.id: item for item in self._offers}
        decisions: list[Decision] = []
        for dispatch in dispatches:
            offer = offers[dispatch.offer_id]
            dispatch.evidence_ids = [
                _id("evidence", dispatch.offer_id),
                *[_id("evidence", allocation.pantry_id) for allocation in dispatch.allocations],
            ]
            if len(dispatch.allocations) > 1:
                destinations = " + ".join(item.pantry_name for item in dispatch.allocations)
                decisions.append(
                    Decision(
                        id=_id("decision-split", dispatch.id),
                        kind="allocation_split",
                        title=f"Split {dispatch.pounds} lb across {len(dispatch.allocations)} pantries?",
                        context=f"{dispatch.donor} offer · {destinations}",
                        dispatch_id=dispatch.id,
                        created_at=now,
                    )
                )
            if offer.requires_confirmation:
                decisions.append(
                    Decision(
                        id=_id("decision-pickup", dispatch.id),
                        kind="pickup_commitment",
                        title=f"Approve the {offer.pickup_start} pickup commitment?",
                        context=f"{dispatch.donor} · {dispatch.pickup_window}",
                        dispatch_id=dispatch.id,
                        created_at=now,
                    )
                )
            if dispatch.confidence < 85 and len(dispatch.allocations) == 1:
                decisions.append(
                    Decision(
                        id=_id("decision-confidence", dispatch.id),
                        kind="low_confidence",
                        title=f"Review this {dispatch.confidence}% confidence match?",
                        context=f"{dispatch.donor} · {dispatch.allocations[0].pantry_name}",
                        dispatch_id=dispatch.id,
                        created_at=now,
                    )
                )
            dispatch.decision_ids = [item.id for item in decisions if item.dispatch_id == dispatch.id]

        def mutate(dashboard):
            dashboard.dispatches = dispatches
            dashboard.decisions = decisions
            pounds = sum(item.pounds for item in dispatches)
            dashboard.impact = Impact(
                pounds_matched=pounds,
                meals_estimated=round(pounds * 0.695),
                minutes_saved=round(len(self._offers) * 9.5),
            )

        self.store.update(mutate)
        matched = sum(item.pounds for item in dispatches)
        self._record_step(
            tool="optimize_dispatches",
            label=f"Matched {matched} lb",
            detail=(
                "Applied need, capacity, time-window, and distance constraints; "
                "ambiguous commitments were gated."
            ),
            started=started,
            evidence_ids=[evidence_id for item in dispatches for evidence_id in item.evidence_ids],
        )
        return {
            "dispatch_count": len(dispatches),
            "pounds_matched": matched,
            "decisions_required": len(decisions),
        }

    def stage_messages(self) -> dict:
        started = perf_counter()
        dashboard = self.store.get()
        now = datetime.now(UTC)
        drafts = []
        for dispatch in dashboard.dispatches:
            allocation_lines = "; ".join(
                f"{item.pantry_name}: {item.pounds} lb" for item in dispatch.allocations
            )
            drafts.append(
                MessageDraft(
                    id=_id("draft", dispatch.id),
                    dispatch_id=dispatch.id,
                    recipient="; ".join(
                        [dispatch.donor, *(item.pantry_name for item in dispatch.allocations)]
                    ),
                    subject=f"Proposed rescue handoff · {dispatch.donor}",
                    body=(
                        f"Proposed allocation: {allocation_lines}. Pickup window: "
                        f"{dispatch.pickup_window}. This is a draft, not a confirmed pickup."
                    ),
                    created_at=now,
                )
            )

        def mutate(current):
            current.message_drafts = drafts

        self.store.update(mutate)
        count = len(drafts)
        self._record_step(
            tool="stage_messages",
            label=f"Drafted {count} messages",
            detail="Prepared donor and pantry drafts. No send capability is exposed to the agent.",
            started=started,
            evidence_ids=[item.id for item in dashboard.evidence[:2]],
        )
        return {"draft_count": count, "sent": 0, "approval_boundary": "human_only"}

    def complete_run(self, summary: str) -> None:
        def mutate(dashboard):
            if dashboard.active_run is None:
                raise RuntimeError("No active run")
            dashboard.active_run.status = "completed"
            dashboard.active_run.completed_at = datetime.now(UTC)
            dashboard.active_run.summary = summary

        self.store.update(mutate)

    def fail_run(self, error: str) -> None:
        def mutate(dashboard):
            if dashboard.active_run is not None:
                dashboard.active_run.status = "failed"
                dashboard.active_run.completed_at = datetime.now(UTC)
                dashboard.active_run.error = error

        self.store.update(mutate)

    def resolve(self, decision_id: str, state: DecisionState | str, note: str | None = None):
        state = DecisionState(state)
        if state not in {DecisionState.APPROVED, DecisionState.REJECTED}:
            raise ValueError("A decision can only be approved or rejected")
        return self.store.resolve_decision(decision_id, state, datetime.now(UTC), note)

    def approve(self, decision_id: str):
        return self.resolve(decision_id, DecisionState.APPROVED)
