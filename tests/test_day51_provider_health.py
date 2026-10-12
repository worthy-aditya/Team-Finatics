from provider_health import ProviderHealth, recommend_provider_for_task, score_provider_health


def test_provider_health_score_basic():
    health = ProviderHealth(
        name="gemini",
        availability=0.95,
        latency_ms=1600,
        cost=2,
        privacy="cloud",
    )

    score = score_provider_health(health)
    assert 0 <= score <= 100
    assert score > 0


def test_recommend_provider_for_private_task_prefers_local():
    recommendations = recommend_provider_for_task(
        task_type="private-analysis",
        is_sensitive=True,
        has_api_key=True,
        provider_scores={
            "gemini": 78,
            "ollama": 91,
        },
    )
    assert recommendations[0]["provider"] == "ollama"


def test_recommend_provider_for_public_cloud_task_prefers_gemini():
    recommendations = recommend_provider_for_task(
        task_type="summarization",
        is_sensitive=False,
        has_api_key=True,
        provider_scores={
            "gemini": 92,
            "ollama": 74,
        },
    )
    assert recommendations[0]["provider"] == "gemini"
