"""Small deterministic eval suite for the judge-facing dispatch scenario."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from rescue_relay.fixtures import demo_offers, demo_pantries
from rescue_relay.matching import match_offers


def main() -> None:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    pantries = demo_pantries()
    dispatches = match_offers(demo_offers(), pantries)
    results: list[dict] = []

    total = sum(item.pounds for item in dispatches)
    results.append(
        {
            "id": cases[0]["id"],
            "passed": total == cases[0]["expected_pounds"]
            and len(dispatches) == cases[0]["expected_dispatches"],
            "observed": {"pounds": total, "dispatches": len(dispatches)},
        }
    )

    harbor = next(item for item in dispatches if item.offer_id == cases[1]["offer_id"])
    results.append(
        {
            "id": cases[1]["id"],
            "passed": len(harbor.allocations) == cases[1]["expected_allocations"]
            and harbor.state == cases[1]["expected_state"],
            "observed": {"allocations": len(harbor.allocations), "state": harbor.state},
        }
    )

    reason_tokens = cases[2]["reason_tokens"]
    grounded = all(
        all(token in allocation.reason for token in reason_tokens)
        for dispatch in dispatches
        for allocation in dispatch.allocations
    )
    results.append({"id": cases[2]["id"], "passed": grounded, "observed": {"grounded": grounded}})

    orchard = next(item for item in dispatches if item.offer_id == cases[3]["offer_id"])
    results.append(
        {
            "id": cases[3]["id"],
            "passed": orchard.pickup_window.startswith(cases[3]["expected_window_prefix"]),
            "observed": {"pickup_window": orchard.pickup_window},
        }
    )

    oversized = deepcopy(demo_offers()[0])
    oversized.pounds = cases[4]["offer_pounds"]
    partial = match_offers([oversized], pantries)[0]
    results.append(
        {
            "id": cases[4]["id"],
            "passed": partial.pounds == cases[4]["expected_matched_pounds"]
            and partial.unallocated_pounds == cases[4]["expected_unallocated_pounds"],
            "observed": {
                "matched_pounds": partial.pounds,
                "unallocated_pounds": partial.unallocated_pounds,
            },
        }
    )

    report = {"passed": all(item["passed"] for item in results), "results": results}
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
