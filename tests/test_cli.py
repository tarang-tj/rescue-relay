from __future__ import annotations

import json
import sys

from rescue_relay import cli


def test_cli_honors_database_environment(monkeypatch, tmp_path, capsys):
    database = tmp_path / "isolated.db"
    monkeypatch.setenv("RESCUERELAY_DB", str(database))
    monkeypatch.setattr(sys, "argv", ["rescue-relay", "dashboard"])

    cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["active_run"] is None
    assert database.exists()


def test_cli_scan_audit_and_reset(monkeypatch, tmp_path, capsys):
    database = tmp_path / "workflow.db"
    monkeypatch.setenv("RESCUERELAY_DB", str(database))

    monkeypatch.setattr(sys, "argv", ["rescue-relay", "scan", "--mode", "demo"])
    cli.main()
    scan = json.loads(capsys.readouterr().out)
    assert scan["active_run"]["status"] == "completed"

    monkeypatch.setattr(sys, "argv", ["rescue-relay", "audit"])
    cli.main()
    audit = json.loads(capsys.readouterr().out)
    assert audit["safety_assertions"]["outbound_send_capability"] is False

    monkeypatch.setattr(sys, "argv", ["rescue-relay", "reset"])
    cli.main()
    reset = json.loads(capsys.readouterr().out)
    assert reset["active_run"] is None
