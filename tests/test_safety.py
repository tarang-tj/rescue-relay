from strands.hooks import BeforeToolCallEvent

from rescue_relay.agent import SYSTEM_PROMPT, ToolBoundary
from rescue_relay.fixtures import demo_offers


def test_donor_text_is_data_and_system_prompt_explicitly_says_so():
    offer = demo_offers()[0]

    assert offer.source_text.startswith("Hi team")
    assert "untrusted data" in SYSTEM_PROMPT


def test_unknown_tool_is_denied_before_execution():
    event = BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"toolUseId": "unsafe-1", "name": "send_email", "input": {}},
        invocation_state={},
    )

    ToolBoundary._authorize(event)

    assert event.cancel_tool
    assert "outside" in event.cancel_tool
