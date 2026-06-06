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
    """Testa se o endpoint /metrics retorna metricas no formato Prometheus."""
    response = client.get('/metrics')
    assert response.status_code == 200
    data = response.get_data(as_text=True)

    # Verifica formato Prometheus (HELP + TYPE + metrica)
    assert '# HELP simples_executions_total' in data
    assert '# TYPE simples_executions_total counter' in data
    assert 'simples_executions_total' in data
    assert '# HELP simples_execution_duration_seconds' in data
    assert '# TYPE simples_execution_duration_seconds histogram' in data
    assert 'simples_execution_duration_seconds' in data
    assert '# HELP simples_active_containers' in data
    assert '# TYPE simples_active_containers gauge' in data
