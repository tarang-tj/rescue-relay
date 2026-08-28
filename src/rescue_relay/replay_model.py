"""A deterministic Strands model for offline demos and CI.

This is not presented as a live foundation-model run. It drives the real Strands agent loop,
real tools, hooks, state transitions, and evidence capture without requiring AWS credentials.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel
from strands.models import Model

T = TypeVar("T", bound=BaseModel)


class ScriptedToolModel(Model):
    def __init__(self, tool_names: Sequence[str]) -> None:
        self._tool_names = list(tool_names)
        self._index = 0

    def get_config(self) -> dict[str, Any]:
        return {"model_id": "deterministic-tool-loop", "context_window_limit": 32_000}

    def update_config(self, **model_config: Any) -> None:
        return None

    async def structured_output(self, output_model: type[T], prompt, system_prompt=None, **kwargs):
        if False:
            yield None

    async def stream(
        self, messages, tool_specs=None, system_prompt=None, **kwargs
    ) -> AsyncGenerator[dict, None]:
        yield {"messageStart": {"role": "assistant"}}
        if self._index < len(self._tool_names):
            name = self._tool_names[self._index]
            tool_id = f"demo-tool-{self._index + 1}"
            yield {"contentBlockStart": {"start": {"toolUse": {"name": name, "toolUseId": tool_id}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps({})}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            text = (
                "Dispatch plan complete. Review the persisted evidence, message drafts, "
                "and any approval decisions."
            )
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": text}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
                "metrics": {"latencyMs": 0},
            }
        }
        self._index += 1
