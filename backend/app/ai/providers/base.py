from typing import Protocol

from ..schemas import LLMResponse, Message, ToolDefinition


class LLMProvider(Protocol):
    def generate(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        ...
