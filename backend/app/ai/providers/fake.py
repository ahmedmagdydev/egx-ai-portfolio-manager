from collections import deque

from ..schemas import LLMResponse, Message


class FakeLLMProvider:
    """Deterministic LLM provider for tests.

    Enqueue one or more `LLMResponse` objects; they are returned in order on
    every call to `generate`.
    """

    def __init__(self, responses: list[LLMResponse] | None = None):
        self._queue: deque[LLMResponse] = deque(responses or [])

    def enqueue(self, response: LLMResponse) -> None:
        self._queue.append(response)

    def generate(
        self,
        messages: list[Message],
        *,
        tools: list | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        if not self._queue:
            return LLMResponse(content="No response queued.")
        return self._queue.popleft()
