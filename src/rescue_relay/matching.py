"""Deterministic allocation engine: the model orchestrates, but cannot invent capacity or matches."""

from __future__ import annotations

from datetime import time, timedelta
from hashlib import sha256

from .domain import Allocation, Dispatch, DispatchState, Offer, Pantry


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{sha256(value.encode()).hexdigest()[:10]}"


def match_offers(offers: list[Offer], pantries: list[Pantry]) -> list[Dispatch]:
    """Allocate each offer by declared need, capacity, distance, and pickup compatibility."""
    dispatches: list[Dispatch] = []
    remaining_capacity = {pantry.id: dict(pantry.capacity) for pantry in pantries}
    reference_date = min((offer.pickup_date for offer in offers), default=None)

    for offer in offers:
        candidates = []
        for pantry in pantries:
            capacity = remaining_capacity[pantry.id].get(offer.category, 0)
            need = pantry.needs.get(offer.category, 0)
            time_ok = time.fromisoformat(pantry.available_start) <= time.fromisoformat(
                offer.pickup_end
            ) and time.fromisoformat(pantry.available_end) >= time.fromisoformat(offer.pickup_start)
            if capacity > 0 and need > 0 and time_ok:
                candidates.append((pantry, min(capacity, need)))
        candidates.sort(key=lambda item: (-item[1], item[0].distance_miles, item[0].name))

        unallocated = offer.pounds
        allocations: list[Allocation] = []
        for pantry, limit in candidates:
            pounds = min(unallocated, limit)
            if pounds <= 0:
                continue
            allocations.append(
                Allocation(
                    pantry_id=pantry.id,
                    pantry_name=pantry.name,
                    pounds=pounds,
                    reason=(
                        f"Needs {pantry.needs[offer.category]} lb; has "
                        f"{remaining_capacity[pantry.id][offer.category]} lb "
                        f"capacity; {pantry.distance_miles:.1f} mi away"
                    ),
                )
            )
            remaining_capacity[pantry.id][offer.category] -= pounds
            unallocated -= pounds
            if unallocated == 0:
                break

        if not allocations:
            continue

        matched_pounds = offer.pounds - unallocated
        coverage = matched_pounds / offer.pounds
        split_penalty = max(0, len(allocations) - 1) * 4
        confidence = round(max(55, 98 * coverage - split_penalty))
        needs_decision = len(allocations) > 1 or confidence < 85 or offer.requires_confirmation
        if reference_date is not None and offer.pickup_date == reference_date:
            day_label = "Today"
        elif reference_date is not None and offer.pickup_date == reference_date + timedelta(days=1):
            day_label = "Tomorrow"
        else:
            day_label = offer.pickup_date.isoformat()
        dispatches.append(
            Dispatch(
                id=_stable_id("dispatch", offer.id),
                offer_id=offer.id,
                donor=offer.donor,
                description=offer.description,
                pounds=matched_pounds,
                offered_pounds=offer.pounds,
                unallocated_pounds=unallocated,
                allocations=allocations,
                pickup_date=offer.pickup_date,
                pickup_window=f"{day_label} {offer.pickup_start}-{offer.pickup_end}",
                confidence=confidence,
                state=(DispatchState.AWAITING_APPROVAL if needs_decision else DispatchState.PROPOSED),
            )
        )
    return dispatches
