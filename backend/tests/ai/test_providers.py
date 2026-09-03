from app.ai.providers.fake import FakeLLMProvider
from app.ai.schemas import LLMResponse, Message, ToolCall


def test_fake_provider_returns_queued_responses() -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(content="first"),
            LLMResponse(content="second"),
        ]
    )
    assert provider.generate([Message(role="user", content="hi")]).content == "first"
    assert provider.generate([Message(role="user", content="hi")]).content == "second"


def test_fake_provider_tool_calls_round_trip() -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="1", name="get_quote", arguments={"symbol": "COMI"})],
                finish_reason="tool_calls",
            )
        ]
    )
    response = provider.generate([Message(role="user", content="price")])
    assert response.finish_reason == "tool_calls"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "get_quote"


def test_fake_provider_empty_queue_safe_default() -> None:
    provider = FakeLLMProvider()
    response = provider.generate([Message(role="user", content="hi")])
    assert response.content == "No response queued."
