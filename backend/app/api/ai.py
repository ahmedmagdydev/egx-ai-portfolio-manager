from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..ai.orchestrator import OrchestratorError, run_analysis
from ..ai.providers.fake import FakeLLMProvider
from ..ai.providers.ollama import OllamaLLMProvider
from ..config import Settings, get_settings
from ..db_session import get_session

router = APIRouter(prefix="/api/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    language: str | None = Field(default=None, max_length=10)
    symbol: str | None = Field(default=None, max_length=20)
    conversation: list[dict[str, str]] | None = None


def _get_provider(settings: Settings):
    if settings.llm_provider == "ollama":
        return OllamaLLMProvider(settings)
    return FakeLLMProvider()


@router.post("/analyze")
def analyze(
    request: AnalyzeRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    provider = _get_provider(settings)
    try:
        result = run_analysis(
            session,
            settings,
            provider,
            request.message,
            language=request.language,
            conversation=request.conversation,
        )
    except OrchestratorError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "LLM_UNAVAILABLE", "message": str(exc)},
        ) from exc
    return result
