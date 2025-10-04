#!/usr/bin/env python3
"""
Test script for ML model integration in RADAR system.
This script tests the ML scorer service integration.
"""

import sys
import os
sys.path.append('/app')

from src.services.ml_scorer import get_ml_scorer
from src.core.logging_config import log

def test_ml_integration():
    """Test ML scorer integration"""
    log.info("Testing ML scorer integration...")

    # Initialize ML scorer
    ml_scorer = get_ml_scorer()

    # Test data - sample articles
    test_articles = [
        {
            "id": "test-1",
            "source_id": 1,
            "title": "Важная новость о росте экономики",
            "content": "Экономика России показывает рост на 3% в этом квартале. Это важный показатель развития.",
            "published_at": "2024-01-01T10:00:00Z",
            "companies": '["Россия"]',
            "people": '[]'
        },
        {
            "id": "test-2",
            "source_id": 2,
            "title": "Кризис в финансовом секторе",
            "content": "Банки сообщают о серьезных проблемах. Кризис может повлиять на всю экономику страны.",
            "published_at": "2024-01-01T11:00:00Z",
            "companies": '["Сбербанк", "ВТБ"]',
            "people": '[]'
        },
        {
            "id": "test-3",
            "source_id": 3,
            "title": "Погода сегодня солнечная",
            "content": "Сегодня ожидается солнечная погода с температурой +25 градусов.",
            "published_at": "2024-01-01T12:00:00Z",
            "companies": '[]',
            "people": '[]'
        }
    ]

    try:
        # Score articles with ML model
        scored_articles = ml_scorer.score_articles(test_articles)

        log.info(f"Successfully scored {len(scored_articles)} articles")

        # Display results
        for article in scored_articles:
            title = article.get('title', 'No title')
            ml_score = article.get('ml_hot_score', 0.0)
            log.info(f"Article: '{title[:50]}...' -> ML Score: {ml_score".3f"}")

        # Test fallback if model not available
        if not ml_scorer.model_available:
            log.warning("ML model not available, used fallback scoring")
        else:
            log.info("ML model scoring successful")

        return True

    except Exception as e:
        log.error(f"ML integration test failed: {e}")
        return False

def test_agent_integration():
    """Test full agent integration with ML scoring"""
    log.info("Testing full agent integration with ML scoring...")

    try:
        from src.agents.graphs import run_analysis

        # Run analysis with small parameters for testing
        results = run_analysis(time_window_hours=720, top_k=2)

        log.info(f"Agent analysis completed with {len(results)} results")

        if results:
            for i, result in enumerate(results, 1):
                log.info(f"Result {i}:")
                log.info(f"  Title: {result.get('headline', 'No title')}")
                log.info(f"  Traditional hotness: {result.get('hotness', 0)".3f"}")
                log.info(f"  ML hotness: {result.get('ml_hotness', 0)".3f"}")
                log.info(f"  Combined hotness: {result.get('combined_hotness', 0)".3f"}")
                log.info(f"  Telegram post: {result.get('telegram_post', 'No post')[:100]}...")

        return True

    except Exception as e:
        log.error(f"Agent integration test failed: {e}")
        return False

if __name__ == "__main__":
    log.info("Starting ML integration tests...")

    # Test ML scorer
    ml_test_passed = test_ml_integration()

    # Test full agent integration (if ML test passed)
    if ml_test_passed:
        agent_test_passed = test_agent_integration()
    else:
        agent_test_passed = False
        log.warning("Skipping agent integration test due to ML scorer failure")

    # Summary
    log.info("=" * 50)
    log.info("INTEGRATION TEST SUMMARY:")
    log.info(f"ML Scorer Test: {'PASSED' if ml_test_passed else 'FAILED'}")
    log.info(f"Agent Integration Test: {'PASSED' if agent_test_passed else 'FAILED'}")

    if ml_test_passed and agent_test_passed:
        log.info("✅ All tests passed! ML integration is working correctly.")
        sys.exit(0)
    else:
        log.error("❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)
