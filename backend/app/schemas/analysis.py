from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecommendationEnum(str, Enum):
    BUY = "BUY"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    SELL = "SELL"
    WATCH = "WATCH"


class AssessmentEnum(str, Enum):
    ATTRACTIVE = "ATTRACTIVE"
    FAIR = "FAIR"
    RICH = "RICH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    FIT = "FIT"
    OVERWEIGHT = "OVERWEIGHT"
    HIGH_CONCENTRATION = "HIGH_CONCENTRATION"
    UNDERWEIGHT = "UNDERWEIGHT"
    NO_POSITION = "NO_POSITION"


class SourceCitation(BaseModel):
    source_type: str
    title: str
    title_ar: str | None = None
    published_at: datetime | None = None
    url: str | None = None


class PortfolioAnalysisResponse(BaseModel):
    symbol: str | None
    recommendation: RecommendationEnum
    confidence: int = Field(..., ge=0, le=100)
    valuation_assessment: AssessmentEnum
    fundamental_assessment: AssessmentEnum
    technical_assessment: AssessmentEnum
    portfolio_assessment: AssessmentEnum
    reasons: list[str]
    reasons_ar: list[str]
    risks: list[str]
    risks_ar: list[str]
    missing_information: list[str]
    missing_information_ar: list[str]
    data_as_of: datetime
    sources: list[SourceCitation]
    interpretation: str | None = None
    language: str = "en"


class HoldingAnalysis(BaseModel):
    symbol: str
    recommendation: RecommendationEnum
    confidence: int = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    reasons: list[str]
    reasons_ar: list[str]


class WholePortfolioAnalysis(BaseModel):
    overall_recommendation: RecommendationEnum
    overall_confidence: int = Field(..., ge=0, le=100)
    concentration_risk: AssessmentEnum
    sector_exposure: AssessmentEnum
    cash_position: AssessmentEnum
    holdings: list[HoldingAnalysis]
    summary_en: str
    summary_ar: str
    data_as_of: datetime
    sources: list[SourceCitation]
    missing_information: list[str]
    missing_information_ar: list[str]
