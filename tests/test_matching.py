from rescue_relay.fixtures import demo_offers, demo_pantries
from rescue_relay.matching import match_offers


def test_matches_every_demo_pound_without_exceeding_capacity():
    dispatches = match_offers(demo_offers(), demo_pantries())

    assert sum(item.pounds for item in dispatches) == 412
    assert len(dispatches) == 4

    used: dict[tuple[str, str], int] = {}
    offers = {item.id: item for item in demo_offers()}
    pantries = {item.id: item for item in demo_pantries()}
    for dispatch in dispatches:
        category = offers[dispatch.offer_id].category
        for allocation in dispatch.allocations:
            key = (allocation.pantry_id, category)
            used[key] = used.get(key, 0) + allocation.pounds

    for (pantry_id, category), pounds in used.items():
        assert pounds <= pantries[pantry_id].capacity[category]


def test_harbor_split_is_exposed_as_ambiguous_not_silently_committed():
    harbor = next(
        item for item in match_offers(demo_offers(), demo_pantries()) if item.offer_id == "offer-harbor"
    )

    assert len(harbor.allocations) == 2
    assert harbor.state == "awaiting_approval"
    assert sum(item.pounds for item in harbor.allocations) == 180


def test_pickup_day_is_not_flattened_to_today():
    orchard = next(
        item for item in match_offers(demo_offers(), demo_pantries()) if item.offer_id == "offer-orchard"
    )

    assert orchard.pickup_window.startswith("Tomorrow ")
    assert orchard.pickup_date.isoformat() == "2026-08-29"


def test_partial_match_exposes_unallocated_remainder():
    offer = demo_offers()[0].model_copy(update={"pounds": 260})
    dispatch = match_offers([offer], demo_pantries())[0]

    assert dispatch.offered_pounds == 260
    assert dispatch.pounds == 200
    assert dispatch.unallocated_pounds == 60
