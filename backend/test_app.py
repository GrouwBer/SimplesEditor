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


def test_compile_empty_code(client):
    """POST /api/compile sem codigo deve retornar 400."""
    response = client.post('/api/compile', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert len(data['errors']) == 1


def test_compile_missing_json(client):
    """POST /api/compile sem JSON deve retornar 400."""
    response = client.post('/api/compile', data='not json',
                           content_type='text/plain')
    assert response.status_code == 400


def test_compile_success(client, mocker):
    """
    POST /api/compile com codigo valido — simplesc retorna 0 e stdout=N NASM.

    Mockamos subprocess.run para nao depender do simplesc real.
    """
    mock_run = mocker.patch('app.subprocess.run')
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = 'section .text\nglobal _start\n_start:\n  mov eax, 1\n  ret\n'

    response = client.post('/api/compile',
                           json={'code': 'programa teste'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'section .text' in data['nasm']


def test_compile_error_with_location(client, mocker):
    """
    POST /api/compile com erro — simplesc retorna != 0 e stderr
    no formato <file>:<line>:<col>: error: <msg>.
    """
    mock_run = mocker.patch('app.subprocess.run')
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = (
        '/tmp/codigo.sim:3:12: error: token inesperado "x"\n'
        '/tmp/codigo.sim:5:1: error: variavel nao declarada\n'
    )

    response = client.post('/api/compile',
                           json={'code': 'codigo com erro'})
    assert response.status_code == 422
    data = response.get_json()
    assert data['status'] == 'error'
    assert len(data['errors']) == 2
    assert data['errors'][0]['line'] == 3
    assert data['errors'][0]['column'] == 12
    assert data['errors'][1]['line'] == 5
    assert data['errors'][1]['column'] == 1


def test_compile_timeout(client, mocker):
    """POST /api/compile com timeout deve retornar 422."""
    import subprocess as sp
    mock_run = mocker.patch('app.subprocess.run')
    mock_run.side_effect = sp.TimeoutExpired(cmd='simplesc', timeout=15)

    response = client.post('/api/compile',
                           json={'code': 'loop infinito'})
    assert response.status_code == 422
    data = response.get_json()
    assert 'tempo limite' in data['errors'][0]['message'].lower()


def test_parse_compile_errors_warning():
    """_parse_compile_errors reconhece warnings."""
    from app import _parse_compile_errors
    errors = _parse_compile_errors(
        '/tmp/x.sim:1:5: warning: variavel nao utilizada\n'
    )
    assert len(errors) == 1
    assert errors[0]['kind'] == 'warning'
    assert errors[0]['line'] == 1
    assert errors[0]['column'] == 5


def test_parse_compile_errors_fallback():
    """_parse_compile_errors faz fallback para mensagens sem formato."""
    from app import _parse_compile_errors
    errors = _parse_compile_errors('segmentation fault (core dumped)\n')
    assert len(errors) == 1
    assert 'message' in errors[0]
    assert 'segmentation' in errors[0]['message']
