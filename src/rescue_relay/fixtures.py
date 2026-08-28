"""Judge-friendly demo fixtures. They are explicit sample data, never presented as live inbox data."""

from datetime import UTC, date, datetime

from .domain import FoodCategory, Offer, Pantry

DEMO_NOW = datetime(2026, 8, 28, 9, 42, tzinfo=UTC)


def demo_offers() -> list[Offer]:
    rows = [
        (
            "offer-harbor",
            "Harbor Market",
            FoodCategory.PRODUCE,
            180,
            "mixed produce",
            date(2026, 8, 28),
            "16:30",
            "17:15",
            True,
            "Hi team — we have about 180 lb of mixed produce (lettuce, carrots, zucchini, apples). "
            "It must be picked up today after 4 PM; our loading dock closes at 5:30.",
        ),
        (
            "offer-sunny",
            "Sunny Bakes",
            FoodCategory.BAKERY,
            48,
            "day-old bread and rolls",
            date(2026, 8, 28),
            "15:00",
            "16:00",
            False,
            "Forty-eight pounds of bread and rolls are boxed and ready between 3 and 4 today.",
        ),
        (
            "offer-green",
            "Green Valley Dairy",
            FoodCategory.DAIRY,
            72,
            "refrigerated dairy",
            date(2026, 8, 28),
            "17:00",
            "18:00",
            False,
            "We can donate 72 lb refrigerated yogurt and milk. Pickup 5-6 PM; cold storage required.",
        ),
        (
            "offer-orchard",
            "Orchard Fresh",
            FoodCategory.PRODUCE,
            112,
            "boxed apples",
            date(2026, 8, 29),
            "09:30",
            "10:15",
            False,
            "Tomorrow morning: 112 lb apples, boxed. Driver can load from 9:30 to 10:15.",
        ),
    ]
    return [
        Offer(
            id=row[0],
            donor=row[1],
            category=row[2],
            pounds=row[3],
            description=row[4],
            pickup_date=row[5],
            pickup_start=row[6],
            pickup_end=row[7],
            requires_confirmation=row[8],
            source_text=row[9],
            received_at=DEMO_NOW,
        )
        for row in rows
    ]


def demo_pantries() -> list[Pantry]:
    return [
        Pantry(
            id="pantry-beacon",
            name="Beacon Pantry",
            needs={FoodCategory.PRODUCE: 140, FoodCategory.DAIRY: 20},
            capacity={FoodCategory.PRODUCE: 120, FoodCategory.DAIRY: 20},
            distance_miles=2.1,
            available_start="14:00",
            available_end="18:00",
        ),
        Pantry(
            id="pantry-riverside",
            name="Riverside Pantry",
            needs={FoodCategory.PRODUCE: 80, FoodCategory.BAKERY: 60},
            capacity={FoodCategory.PRODUCE: 80, FoodCategory.BAKERY: 60},
            distance_miles=3.8,
            available_start="13:00",
            available_end="18:00",
        ),
        Pantry(
            id="pantry-community",
            name="Community Table",
            needs={FoodCategory.DAIRY: 90},
            capacity={FoodCategory.DAIRY: 80},
            distance_miles=4.4,
            available_start="16:00",
            available_end="19:00",
        ),
        Pantry(
            id="pantry-northside",
            name="Northside Pantry",
            needs={FoodCategory.PRODUCE: 160},
            capacity={FoodCategory.PRODUCE: 150},
            distance_miles=5.2,
            available_start="08:00",
            available_end="12:00",
        ),
    ]
