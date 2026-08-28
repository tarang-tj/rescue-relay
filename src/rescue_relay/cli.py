from __future__ import annotations

import argparse
import json
import os

from .agent import run_agent
from .service import DispatchService
from .store import StateStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RescueRelay")
    parser.add_argument("command", choices=["scan", "dashboard", "reset", "audit"])
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--database", default=os.getenv("RESCUERELAY_DB", "data/rescue_relay.db"))
    args = parser.parse_args()
    store = StateStore(args.database)
    service = DispatchService(store)
    if args.command == "scan":
        run_agent(service, args.mode)
    elif args.command == "reset":
        store.reset()
    payload = store.get().model_dump(mode="json")
    if args.command == "audit":
        payload = {
            "schema_version": "1.0",
            "safety_assertions": {
                "outbound_send_capability": False,
                "commitments_require_persisted_approval": True,
            },
            "dashboard": payload,
        }
    print(json.dumps(payload, indent=2))
