
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.ai.orchestrator import run_analysis
from app.ai.providers.fake import FakeLLMProvider
from app.ai.schemas import LLMResponse, ToolCall
from app.config import Settings
from app.main import create_app


@pytest.fixture
def orchestrator_session():
    app = create_app()
    with TestClient(app) as _client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE document_chunks, documents, financial_statements, "
                    "stock_prices, price_snapshots, transactions, stocks "
                    "RESTART IDENTITY CASCADE"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO stocks (id, symbol, name_en, currency, is_active, created_at) "
                    "VALUES (gen_random_uuid(), 'COMI', 'Commercial International Bank', "
                    "'EGP', true, NOW())"
                )
            )
        factory = __import__("sqlalchemy.orm", fromlist=["sessionmaker"]).sessionmaker(
            bind=app.state.engine, expire_on_commit=False
        )
        with factory() as session:
            yield session


def test_orchestrator_executes_quote_tool(orchestrator_session) -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="tc1", name="get_quote", arguments={"symbol": "COMI"})],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="The latest COMI quote is available.", finish_reason="stop"),
        ]
    )
    result = run_analysis(
        orchestrator_session,
        Settings(),
        provider,
        "What is the latest COMI price?",
    )
    assert result["language"] == "en"
    assert any(tc["name"] == "get_quote" for tc in result["tool_calls"])
    facts = result["verified_facts"]
    assert any(fact.get("symbol") == "COMI" for fact in facts)


def test_orchestrator_detects_arabic(orchestrator_session) -> None:
    provider = FakeLLMProvider(responses=[LLMResponse(content="تحليل COMI متاح.")])
    result = run_analysis(
        orchestrator_session,
        Settings(),
        provider,
        "حلل COMI",
    )
    assert result["language"] == "ar"


def test_orchestrator_rejects_unknown_tool(orchestrator_session) -> None:
    provider = FakeLLMProvider(
        responses=[
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="tc2", name="run_shell", arguments={"cmd": "ls"})],
                finish_reason="tool_calls",
            ),
            LLMResponse(content="I cannot run that tool.", finish_reason="stop"),
        ]
    )
    result = run_analysis(
        orchestrator_session,
        Settings(),
        provider,
        "Run a shell command.",
    )
    assert any("Unknown or forbidden tool" in warning for warning in result["warnings"])


def test_orchestrator_empty_queue_returns_safe_response(orchestrator_session) -> None:
    provider = FakeLLMProvider(responses=[])
    result = run_analysis(orchestrator_session, Settings(), provider, "Hello")
    assert "interpretation" in result
    assert result["tool_calls"] == []
