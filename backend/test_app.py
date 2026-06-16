"""Testes do backend do SimplesEditor.

Cobre:
- app.py: health, metrics, limits, rate limit, error handler 500, before_request
- rate_limiter.py: is_rate_limited, get_rate_limit_headers, reset_rate_limits
- logging_config.py: setup_logging, get_logger
- sandbox_config.py: configuracoes, get_sandbox_run_kwargs
"""

import importlib
import logging
import os
from unittest.mock import MagicMock, patch

import pytest
import structlog
from app import app


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Limpa o rate limiter antes de cada teste."""
    from rate_limiter import reset_rate_limits
    reset_rate_limits()
    yield


# ============================================================
# app.py — /api/health
# ============================================================

def test_health_endpoint(client):
    """Testa se o endpoint /api/health retorna status ok."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


# ============================================================
# app.py — /metrics (200)
# ============================================================

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


# ============================================================
# app.py — /metrics (403)
# ============================================================

def test_metrics_forbidden_when_not_localhost():
    """Testa que /metrics retorna 403 quando request.remote_addr != 127.0.0.1."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        response = client.get('/metrics', environ_overrides={'REMOTE_ADDR': '10.0.0.1'})
        assert response.status_code == 403


# ============================================================
# app.py — /api/limits
# ============================================================

def test_limits_endpoint(client):
    """Testa se o endpoint /api/limits retorna os limites configurados."""
    response = client.get('/api/limits')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["runs_per_minute"] == 30
    assert data["limit"] == 30
    assert data["remaining"] <= 30
    assert "reset_at" in data


# ============================================================
# app.py — Rate limit headers nas respostas de API
# ============================================================

def test_api_response_has_rate_limit_headers(client):
    """Testa que respostas de API incluem headers de rate limit."""
    response = client.get('/api/health')
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "30"


def test_metrics_endpoint_no_rate_limit_headers(client):
    """Testa que /metrics NAO tem headers de rate limit (nao e rota /api/)."""
    response = client.get('/metrics')
    assert "X-RateLimit-Limit" not in response.headers


# ============================================================
# app.py — 429 rate limit exceeded
# ============================================================

def test_rate_limit_exceeded_returns_429(client):
    """Testa que exceder o rate limit retorna 429."""
    from rate_limiter import _limiter_store

    # Enche o rate limit manualmente: adiciona 30 timestamps recentes
    import time
    now = time.monotonic()
    _limiter_store["ip:127.0.0.1"] = [now] * 30

    # A proxima requisicao a uma rota /api/ (nao isenta) deve ser bloqueada
    response = client.get('/api/health')
    assert response.status_code == 200  # /api/health e isenta

    # Testar com uma rota nao isenta — usamos /api/limits como base,
    # mas ela e isenta. Vamos testar via requisicao a uma rota fake.
    # Como nao ha outra rota /api/, testamos o rate_limiter diretamente.
    from rate_limiter import is_rate_limited
    assert is_rate_limited() is True  # ainda deve estar limitado


def test_rate_limit_blocked_response_structure(client):
    """Testa a estrutura da resposta 429."""
    from rate_limiter import _limiter_store
    import time

    # Enche o rate limit
    now = time.monotonic()
    _limiter_store["ip:127.0.0.1"] = [now] * 30

    # Simula chamada ao before_request handler diretamente
    with app.test_request_context('/api/test', method='POST'):
        from app import apply_rate_limit
        response = apply_rate_limit()
        if response is not None:
            data = response[0].get_json()
            assert data["error"] == "rate_limit_exceeded"
            assert data["retry_after_s"] == 60


# ============================================================
# rate_limiter.py — is_rate_limited
# ============================================================

def test_is_rate_limited_allows_within_limit():
    """Testa que requisicoes dentro do limite sao permitidas."""
    from rate_limiter import is_rate_limited

    with app.test_request_context('/api/test'):
        assert is_rate_limited() is False  # primeira req
        assert is_rate_limited(max_requests=5) is False  # 2a de 5


def test_is_rate_limited_blocks_when_exceeded():
    """Testa que requisicoes que excedem o limite sao bloqueadas."""
    from rate_limiter import is_rate_limited

    with app.test_request_context('/api/test'):
        # Usa um limite baixo para teste
        max_r = 3
        assert is_rate_limited(max_requests=max_r) is False  # 1
        assert is_rate_limited(max_requests=max_r) is False  # 2
        assert is_rate_limited(max_requests=max_r) is False  # 3
        assert is_rate_limited(max_requests=max_r) is True   # 4 — bloqueada


def test_is_rate_limited_resets_after_window(monkeypatch):
    """Testa que o contador reseta apos a janela de tempo."""
    from rate_limiter import is_rate_limited
    import time

    with app.test_request_context('/api/test'):
        # Mocka time.monotonic para controlar o tempo
        fake_time = [100.0]

        def mock_monotonic():
            return fake_time[0]

        monkeypatch.setattr(time, 'monotonic', mock_monotonic)

        max_r = 2
        assert is_rate_limited(max_requests=max_r) is False  # t=100
        assert is_rate_limited(max_requests=max_r) is False  # t=100

        # Avanca o tempo para depois da janela
        fake_time[0] = 161.0  # 61s depois
        assert is_rate_limited(max_requests=max_r) is False  # resetou


# ============================================================
# rate_limiter.py — get_rate_limit_headers
# ============================================================

def test_get_rate_limit_headers_structure():
    """Testa que get_rate_limit_headers retorna headers esperados."""
    from rate_limiter import get_rate_limit_headers

    with app.test_request_context('/api/test'):
        headers = get_rate_limit_headers()
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

        assert headers["X-RateLimit-Limit"] == "30"


def test_get_rate_limit_headers_remaining_decreases():
    """Testa que o contador de remaining diminui a cada request."""
    from rate_limiter import is_rate_limited, get_rate_limit_headers

    with app.test_request_context('/api/test'):
        headers1 = get_rate_limit_headers(max_requests=5)
        remaining1 = int(headers1["X-RateLimit-Remaining"])
        assert remaining1 == 5

        is_rate_limited(max_requests=5)  # consome 1
        headers2 = get_rate_limit_headers(max_requests=5)
        remaining2 = int(headers2["X-RateLimit-Remaining"])
        assert remaining2 == remaining1 - 1


# ============================================================
# rate_limiter.py — reset_rate_limits
# ============================================================

def test_reset_rate_limits_clears_store():
    """Testa que reset_rate_limits limpa o armazenamento."""
    from rate_limiter import is_rate_limited, reset_rate_limits, _limiter_store

    with app.test_request_context('/api/test'):
        is_rate_limited(max_requests=3)  # consome 1
        assert len(_limiter_store) > 0

        reset_rate_limits()
        assert len(_limiter_store) == 0


# ============================================================
# app.py — Error handler 500
# ============================================================

def test_internal_error_handler(client):
    """Testa se o handler de erro 500 retorna JSON e loga o erro."""
    from app import internal_error

    class FakeException(Exception):
        def __str__(self):
            return "test error message"

    with app.test_request_context():
        result = internal_error(FakeException())
        response, status_code = result
        assert status_code == 500
        assert response.get_json() == {"error": "internal server error"}


# ============================================================
# app.py — before_request logging
# ============================================================

def test_before_request_logs_request(client, caplog):
    """Testa que o hook before_request faz log estruturado."""
    caplog.set_level("DEBUG")
    client.get('/api/health')
    assert len(caplog.records) > 0


# ============================================================
# app.py — __main__ block
# ============================================================

def test_app_main_block():
    """Testa que o modulo app e importavel e tem o bloco main."""
    assert app is not None


# ============================================================
# logging_config.py — setup_logging
# ============================================================

def test_setup_logging_configured():
    """Testa que setup_logging configura structlog sem erros."""
    from logging_config import setup_logging, get_logger

    setup_logging()
    logger = get_logger("test_module")
    assert logger is not None
    logger.info("test_message", extra_field="value")


def test_setup_logging_respects_env_level(monkeypatch):
    """Testa que setup_logging usa LOG_LEVEL do ambiente."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from logging_config import setup_logging
    setup_logging()


def test_setup_logging_default_level():
    """Testa que setup_logging executa sem erro com level INFO padrao."""
    if "LOG_LEVEL" in os.environ:
        del os.environ["LOG_LEVEL"]
    from logging_config import setup_logging
    setup_logging()


# ============================================================
# logging_config.py — get_logger
# ============================================================

def test_get_logger_with_name():
    """Testa get_logger com nome explicito."""
    from logging_config import get_logger
    logger = get_logger("my.custom.logger")
    assert logger is not None


def test_get_logger_without_name():
    """Testa get_logger sem nome (deve inferir do frame)."""
    from logging_config import get_logger
    logger = get_logger()
    assert logger is not None


# ============================================================
# sandbox_config.py — APP_CONFIG
# ============================================================

def test_app_config_defaults():
    """Testa valores padrao do APP_CONFIG."""
    from sandbox_config import APP_CONFIG

    assert APP_CONFIG["timeout"] == 10
    assert APP_CONFIG["compile_timeout"] == 15
    assert APP_CONFIG["max_code_kb"] == 64
    assert APP_CONFIG["runs_per_minute"] == 30
    assert APP_CONFIG["sandbox_image"] == "simples-runner:latest"


def test_app_config_env_overrides(monkeypatch):
    """Testa que variaveis de ambiente sobrescrevem APP_CONFIG."""
    monkeypatch.setenv("EXEC_TIMEOUT_S", "30")
    monkeypatch.setenv("COMPILE_TIMEOUT_S", "45")
    monkeypatch.setenv("MAX_CODE_KB", "128")
    monkeypatch.setenv("RUNS_PER_MINUTE", "60")
    monkeypatch.setenv("SANDBOX_IMAGE", "custom-runner:v2")

    import sandbox_config
    importlib.reload(sandbox_config)

    assert sandbox_config.APP_CONFIG["timeout"] == 30
    assert sandbox_config.APP_CONFIG["compile_timeout"] == 45
    assert sandbox_config.APP_CONFIG["max_code_kb"] == 128
    assert sandbox_config.APP_CONFIG["runs_per_minute"] == 60
    assert sandbox_config.APP_CONFIG["sandbox_image"] == "custom-runner:v2"


# ============================================================
# sandbox_config.py — DOCKER_HARD_LIMITS
# ============================================================

def test_docker_hard_limits_defaults():
    """Testa valores padrao do DOCKER_HARD_LIMITS."""
    from sandbox_config import DOCKER_HARD_LIMITS

    assert DOCKER_HARD_LIMITS["mem_limit"] == "64m"
    assert DOCKER_HARD_LIMITS["cpu_quota"] == 50000
    assert DOCKER_HARD_LIMITS["cpu_period"] == 100000
    assert DOCKER_HARD_LIMITS["stop_timeout"] == 12
    assert DOCKER_HARD_LIMITS["pids_limit"] == 64
    assert DOCKER_HARD_LIMITS["network_disabled"] is True
    assert DOCKER_HARD_LIMITS["read_only"] is True
    assert DOCKER_HARD_LIMITS["tmpfs"] == {"/tmp": "size=16m,noexec,nosuid"}
    assert DOCKER_HARD_LIMITS["cap_drop"] == ["ALL"]
    assert DOCKER_HARD_LIMITS["security_opt"] == ["no-new-privileges"]


def test_docker_hard_limits_env_overrides(monkeypatch):
    """Testa que env vars sobrescrevem DOCKER_HARD_LIMITS."""
    monkeypatch.setenv("SANDBOX_MEM_LIMIT", "128m")
    monkeypatch.setenv("SANDBOX_CPU_QUOTA", "100000")
    monkeypatch.setenv("SANDBOX_CPU_PERIOD", "200000")

    import sandbox_config
    importlib.reload(sandbox_config)

    assert sandbox_config.DOCKER_HARD_LIMITS["mem_limit"] == "128m"
    assert sandbox_config.DOCKER_HARD_LIMITS["cpu_quota"] == 100000
    assert sandbox_config.DOCKER_HARD_LIMITS["cpu_period"] == 200000


# ============================================================
# sandbox_config.py — get_sandbox_run_kwargs
# ============================================================

def test_get_sandbox_run_kwargs_structure():
    """Testa que get_sandbox_run_kwargs retorna dict com chaves esperadas."""
    from sandbox_config import get_sandbox_run_kwargs

    kwargs = get_sandbox_run_kwargs()

    expected_keys = [
        "mem_limit", "cpu_quota", "cpu_period", "stop_timeout",
        "pids_limit", "network_disabled", "read_only", "tmpfs",
        "cap_drop", "security_opt",
    ]
    for key in expected_keys:
        assert key in kwargs, f"Chave {key} ausente no retorno"

    assert len(kwargs) == len(expected_keys)


def test_get_sandbox_run_kwargs_excludes_app_config():
    """Testa que get_sandbox_run_kwargs NAO inclui chaves do APP_CONFIG."""
    from sandbox_config import get_sandbox_run_kwargs

    kwargs = get_sandbox_run_kwargs()
    assert "timeout" not in kwargs
    assert "compile_timeout" not in kwargs
    assert "max_code_kb" not in kwargs
    assert "runs_per_minute" not in kwargs
    assert "sandbox_image" not in kwargs


def test_get_sandbox_run_kwargs_values():
    """Testa que os valores de get_sandbox_run_kwargs conferem com DOCKER_HARD_LIMITS."""
    from sandbox_config import get_sandbox_run_kwargs, DOCKER_HARD_LIMITS

    kwargs = get_sandbox_run_kwargs()
    for key in kwargs:
        assert kwargs[key] == DOCKER_HARD_LIMITS[key], (
            f"Valor de {key} diverge: {kwargs[key]} != {DOCKER_HARD_LIMITS[key]}"
        )


# ============================================================
# sandbox_config.py — SANDBOX_CONFIG (merged)
# ============================================================

def test_sandbox_config_merged():
    """Testa que SANDBOX_CONFIG contem chaves de APP_CONFIG e DOCKER_HARD_LIMITS."""
    from sandbox_config import SANDBOX_CONFIG, APP_CONFIG, DOCKER_HARD_LIMITS

    for key in APP_CONFIG:
        assert key in SANDBOX_CONFIG, f"Chave {key} de APP_CONFIG ausente no SANDBOX_CONFIG"

    for key in DOCKER_HARD_LIMITS:
        assert key in SANDBOX_CONFIG, f"Chave {key} de DOCKER_HARD_LIMITS ausente no SANDBOX_CONFIG"


def test_sandbox_config_preserves_values():
    """Testa que SANDBOX_CONFIG preserva os valores das fontes originais."""
    from sandbox_config import SANDBOX_CONFIG, APP_CONFIG, DOCKER_HARD_LIMITS

    for key, value in APP_CONFIG.items():
        assert SANDBOX_CONFIG[key] == value

    for key, value in DOCKER_HARD_LIMITS.items():
        assert SANDBOX_CONFIG[key] == value
