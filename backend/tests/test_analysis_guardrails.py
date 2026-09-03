from app.services.portfolio_ai import _contains_forbidden_phrases


def test_detects_forbidden_arabic_phrases() -> None:
    assert _contains_forbidden_phrases("السهم مضمون")
    assert _contains_forbidden_phrases("أرباح مضمونة")
    assert _contains_forbidden_phrases("سيرتفع بنسبة 10%")


def test_detects_forbidden_english_phrases() -> None:
    assert _contains_forbidden_phrases("This is a guaranteed return.")
    assert _contains_forbidden_phrases("probability that the stock will rise")


def test_allows_neutral_phrases() -> None:
    assert not _contains_forbidden_phrases("The stock may rise or fall.")
    assert not _contains_forbidden_phrases("Decision-support analysis only.")
