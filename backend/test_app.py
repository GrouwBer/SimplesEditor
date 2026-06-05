import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Testa se o endpoint /api/health retorna status ok."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_endpoint(client):
    """Testa se o endpoint /metrics retorna metricas Prometheus."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'simples_executions_total' in response.get_data(as_text=True)
    assert 'simples_execution_duration_seconds' in response.get_data(as_text=True)
