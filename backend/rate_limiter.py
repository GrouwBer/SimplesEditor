"""
Rate limiter para o SimplesEditor.

Implementa limitacao de taxa por usuario (via JWT sub) e por IP.
Usa um dicionario em memoria com janela deslizante (sliding window).
Configuracao via sandbox_config.APP_CONFIG["runs_per_minute"].
"""

import time
import threading
from typing import Callable
from functools import wraps

from flask import request, jsonify, g

from sandbox_config import APP_CONFIG


# Pool de rate limiters por chave (user_id ou IP)
# Estrutura: {key: [timestamps]}
_limiter_store: dict[str, list[float]] = {}
_lock = threading.Lock()


def _get_client_ip() -> str:
    """Extrai o IP real do cliente, considerando proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _get_rate_limit_key() -> str:
    """
    Retorna a chave de rate limit: user_id (se JWT disponivel) ou IP.

    Quando o decorator verify_jwt estiver implementado, ele deve
    definir g.user_id. Se presente, usamos como chave.
    """
    user_id = g.get("user_id")
    if user_id:
        return f"user:{user_id}"
    return f"ip:{_get_client_ip()}"


def _cleanup_expired(window_s: float = 60):
    """Remove entradas expiradas do armazenamento."""
    cutoff = time.monotonic() - window_s
    with _lock:
        expired_keys = []
        for key, timestamps in _limiter_store.items():
            # Filtra timestamps dentro da janela
            active = [t for t in timestamps if t > cutoff]
            if active:
                _limiter_store[key] = active
            else:
                expired_keys.append(key)
        for key in expired_keys:
            del _limiter_store[key]


def is_rate_limited(max_requests: int | None = None, window_s: int = 60) -> bool:
    """
    Verifica se a requisicao atual deve ser limitada.

    Args:
        max_requests: maximo de requisicoes permitidas na janela.
                      Se None, usa o valor de APP_CONFIG["runs_per_minute"].
        window_s: tamanho da janela deslizante em segundos.

    Returns:
        True se a requisicao excedeu o limite, False caso contrario.
    """
    if max_requests is None:
        max_requests = APP_CONFIG["runs_per_minute"]

    key = _get_rate_limit_key()
    now = time.monotonic()
    cutoff = now - window_s

    with _lock:
        if key not in _limiter_store:
            _limiter_store[key] = []

        # Filtra timestamps dentro da janela
        _limiter_store[key] = [t for t in _limiter_store[key] if t > cutoff]

        # Verifica limite
        if len(_limiter_store[key]) >= max_requests:
            return True

        # Registra a requisicao
        _limiter_store[key].append(now)

    return False


def rate_limit(max_requests: int | None = None, window_s: int = 60) -> Callable:
    """
    Decorator que aplica rate limit a uma rota do Flask.

    Uso:
        @app.route('/api/execute')
        @rate_limit()
        def execute():
            ...

    Args:
        max_requests: maximo de requisicoes permitidas na janela.
        window_s: tamanho da janela deslizante em segundos.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            if is_rate_limited(max_requests, window_s):
                retry_after = window_s
                return jsonify({
                    "error": "rate_limit_exceeded",
                    "retry_after_s": retry_after,
                }), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_remaining_requests(max_requests: int | None = None, window_s: int = 60) -> int:
    """
    Retorna quantas requisicoes ainda pode fazer na janela atual.
    """
    if max_requests is None:
        max_requests = APP_CONFIG["runs_per_minute"]

    key = _get_rate_limit_key()
    now = time.monotonic()
    cutoff = now - window_s

    with _lock:
        if key not in _limiter_store:
            return max_requests
        active = [t for t in _limiter_store[key] if t > cutoff]
        return max(0, max_requests - len(active))


def get_rate_limit_headers(max_requests: int | None = None, window_s: int = 60) -> dict:
    """
    Retorna headers de rate limit padronizados.
    """
    if max_requests is None:
        max_requests = APP_CONFIG["runs_per_minute"]
    remaining = get_remaining_requests(max_requests, window_s)
    return {
        "X-RateLimit-Limit": str(max_requests),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(time.time() + window_s)),
    }


def reset_rate_limits():
    """Limpa todos os rate limiters (util em testes)."""
    with _lock:
        _limiter_store.clear()
