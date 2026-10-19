import pytest
from app.config import get_settings


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "database" in data
    assert "stt_provider" in data
    assert "llm_provider" in data
    assert "voice_engine" in data
    assert "mock_ai" in data
    assert "stt_status" in data
    assert "llm_status" in data
    assert "voice_status" in data
