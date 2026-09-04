import asyncio
from app.services.priority_scorer import PriorityScorer


def test_priority_scorer_low():
    scorer = PriorityScorer()
    score, tier = asyncio.run(scorer.calculate_priority(severity=1, cluster_size=0, days_open=0))
    assert score == 15.0
    assert tier == "LOW"


def test_priority_scorer_medium():
    scorer = PriorityScorer()
    score, tier = asyncio.run(scorer.calculate_priority(severity=3, cluster_size=1, days_open=2))
    assert score == 49.0
    assert tier == "MEDIUM"


def test_priority_scorer_critical():
    scorer = PriorityScorer()
    score, tier = asyncio.run(scorer.calculate_priority(severity=5, cluster_size=5, days_open=15))
    assert score == 97.5
    assert tier == "CRITICAL"


def test_priority_scorer_clamping():
    scorer = PriorityScorer()
    score, tier = asyncio.run(scorer.calculate_priority(severity=5, cluster_size=20, days_open=50))
    assert score == 100.0
    assert tier == "CRITICAL"
