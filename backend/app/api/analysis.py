from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..ai.providers.fake import FakeLLMProvider
from ..ai.providers.ollama import OllamaLLMProvider
from ..config import Settings, get_settings
from ..db_session import get_session
from ..schemas.analysis import PortfolioAnalysisResponse, WholePortfolioAnalysis
from ..services.portfolio_ai import analyze_portfolio, analyze_stock

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class StockAnalysisRequest(BaseModel):
    include_portfolio_context: bool = True
    language: str = "en"


class PortfolioAnalysisRequest(BaseModel):
    language: str = "en"


def _get_provider(settings: Settings):
    if settings.llm_provider == "ollama":
        return OllamaLLMProvider(settings)
    return FakeLLMProvider()


@router.post("/stock/{symbol}", response_model=PortfolioAnalysisResponse)
def analyze_stock_endpoint(
    symbol: str,
    request: StockAnalysisRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PortfolioAnalysisResponse:
    provider = _get_provider(settings)
    try:
        return analyze_stock(
            session,
            settings,
            provider,
            symbol,
            include_portfolio=request.include_portfolio_context,
            language=request.language,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_UNAVAILABLE", "message": str(exc)},
        ) from exc


@router.post("/portfolio", response_model=WholePortfolioAnalysis)
def analyze_portfolio_endpoint(
    request: PortfolioAnalysisRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> WholePortfolioAnalysis:
    provider = _get_provider(settings)
    try:
        return analyze_portfolio(session, settings, provider, language=request.language)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_UNAVAILABLE", "message": str(exc)},
        ) from exc
