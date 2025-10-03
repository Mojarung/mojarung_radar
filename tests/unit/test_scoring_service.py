import pytest

from src.services.scoring_service import ScoringService


@pytest.mark.asyncio
async def test_calculate_hotness_basic():
    service = ScoringService()
    
    hotness = await service.calculate_hotness(
        unexpectedness=0.8,
        materiality=0.9,
        velocity=0.7,
        breadth=0.6,
        credibility=0.8,
    )
    
    assert 0.0 <= hotness.value <= 1.0
    assert hotness.unexpectedness == 0.8
    assert hotness.materiality == 0.9


@pytest.mark.asyncio
async def test_calculate_hotness_zero():
    service = ScoringService()
    
    hotness = await service.calculate_hotness(
        unexpectedness=0.0,
        materiality=0.0,
        velocity=0.0,
        breadth=0.0,
        credibility=0.0,
    )
    
    assert hotness.value == 0.0

