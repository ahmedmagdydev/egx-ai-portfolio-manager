import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AssessmentEnum,
    PortfolioAnalysisResponse,
    RecommendationEnum,
    SourceCitation,
)


def test_valid_portfolio_analysis_response() -> None:
    response = PortfolioAnalysisResponse(
        symbol="COMI",
        recommendation=RecommendationEnum.HOLD,
        confidence=72,
        valuation_assessment=AssessmentEnum.FAIR,
        fundamental_assessment=AssessmentEnum.POSITIVE,
        technical_assessment=AssessmentEnum.BULLISH,
        portfolio_assessment=AssessmentEnum.FIT,
        reasons=["Solid fundamentals"],
        reasons_ar=["أساسيات قوية"],
        risks=["Market risk"],
        risks_ar=["مخاطر السوق"],
        missing_information=[],
        missing_information_ar=[],
        data_as_of="2025-01-15T10:00:00+00:00",
        sources=[
            SourceCitation(
                source_type="MARKET_DATA",
                title="COMI Quote",
                published_at="2025-01-15T10:00:00+00:00",
            )
        ],
        language="ar",
    )
    assert response.symbol == "COMI"
    assert response.language == "ar"


def test_confidence_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        PortfolioAnalysisResponse(
            symbol="COMI",
            recommendation=RecommendationEnum.HOLD,
            confidence=150,
            valuation_assessment=AssessmentEnum.FAIR,
            fundamental_assessment=AssessmentEnum.POSITIVE,
            technical_assessment=AssessmentEnum.BULLISH,
            portfolio_assessment=AssessmentEnum.FIT,
            reasons=[],
            reasons_ar=[],
            risks=[],
            risks_ar=[],
            missing_information=[],
            missing_information_ar=[],
            data_as_of="2025-01-15T10:00:00+00:00",
            sources=[],
        )


def test_recommendation_labels_have_arabic_equivalents() -> None:
    labels = {
        "BUY": "شراء",
        "ACCUMULATE": "تراكم",
        "HOLD": "احتفاظ",
        "REDUCE": "تقليل",
        "SELL": "بيع",
        "WATCH": "مراقبة",
    }
    assert all(RecommendationEnum(k) for k in labels)
