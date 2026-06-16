from flask import Flask, jsonify, request, abort
import os
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from logging_config import setup_logging, get_logger
from rate_limiter import is_rate_limited, get_rate_limit_headers

# Inicializar logs estruturados
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)

# Registrar endpoint WebSocket /ws/run
from ws_handler import register_websocket
register_websocket(app)

# Metricas Prometheus — prefixo `simples_` evita colisao com outras apps

# Contador de execucoes por status (success, error, timeout)
EXECUTIONS_TOTAL = Counter(
    'simples_executions_total',
    'Total de execucoes de codigo',
    ['status']
)

# Duracao das execucoes (histograma com buckets pre-definidos)
EXECUTION_DURATION = Histogram(
    'simples_execution_duration_seconds',
    'Duracao das execucoes em segundos',
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

# Contador de compilacoes por status (success, error)
COMPILATIONS_TOTAL = Counter(
    'simples_compilations_total',
    'Total de compilacoes',
    ['status']
)

# Container ativos (Gauge: inc ao criar, dec ao destruir)
ACTIVE_CONTAINERS = Gauge(
    'simples_active_containers',
    'Numero de containers sandbox ativos no momento',
)

# Contador de rate limit excedido
RATE_LIMIT_EXCEEDED = Counter(
    'simples_rate_limit_exceeded_total',
    'Total de requisicoes rejeitadas por rate limit',
    ['limit_type']
)


@app.before_request
def log_request():
    """Log estruturado de cada request."""
    logger.info(
        "request_started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
    )


# Rotas que nao devem ter rate limit aplicado
_RATE_LIMIT_EXEMPT_PATHS = ('/api/health', '/metrics', '/api/limits')


@app.before_request
def apply_rate_limit():
    """Aplica rate limit em requisicoes a rotas de execucao."""
    if request.path.startswith('/api/') and request.path not in _RATE_LIMIT_EXEMPT_PATHS:
        if is_rate_limited():
            RATE_LIMIT_EXCEEDED.labels(limit_type='api').inc()
            logger.warning("rate_limit_exceeded", path=request.path)
            return jsonify({
                "error": "rate_limit_exceeded",
                "retry_after_s": 60,
            }), 429, {'Content-Type': 'application/json'}


@app.after_request
def add_rate_limit_headers(response):
    """Adiciona headers de rate limit a todas as respostas de API."""
    if request.path.startswith('/api/'):
        headers = get_rate_limit_headers()
        for key, value in headers.items():
            response.headers[key] = value
    return response


@app.route('/api/health')
def health():
    logger.debug("health_check")
    return jsonify({"status": "ok"})


@app.route('/api/limits')
def limits():
    """Retorna os limites de taxa configurados e o saldo restante."""
    from sandbox_config import APP_CONFIG as cfg
    headers = get_rate_limit_headers()
    return jsonify({
        "runs_per_minute": cfg["runs_per_minute"],
        "limit": int(headers["X-RateLimit-Limit"]),
        "remaining": int(headers["X-RateLimit-Remaining"]),
        "reset_at": headers["X-RateLimit-Reset"],
    })


@app.route('/api/compile', methods=['POST'])
def compile_code():
    """
    Endpoint de compilacao SIMPLES → NASM → ELF.

    Recebe codigo fonte SIMPLES, executa o pipeline de compilacao
    e retorna o NASM gerado ou erros com linha/coluna.
    """
    from compiler import compile_source

    data = request.get_json(silent=True)
    if not data or "code" not in data:
        return jsonify({"error": "campo 'code' obrigatorio"}), 400

    source_code = data["code"]

    # Valida tamanho maximo
    from sandbox_config import APP_CONFIG
    max_kb = APP_CONFIG["max_code_kb"]
    if len(source_code.encode("utf-8")) > max_kb * 1024:
        return jsonify({
            "error": f"codigo excede o limite de {max_kb}KB"
        }), 413

    result = compile_source(source_code)

    if result.success:
        return jsonify({
            "success": True,
            "nasm": result.nasm_output,
            "binary_path": result.binary_path,
            "duration_s": round(result.duration_s, 3),
        })
    else:
        return jsonify({
            "success": False,
            "errors": result.errors,
            "nasm": result.nasm_output,
            "duration_s": round(result.duration_s, 3),
        })


@app.route('/metrics')
def metrics():
    """
    Endpoint Prometheus.

    Protegido em duas camadas:
    1. Nginx bloqueia acesso externo (defense in depth)
    2. Safety net: aborta se nao for localhost
    """
    if request.remote_addr != '127.0.0.1':
        abort(403)
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.errorhandler(500)
def internal_error(e):
    logger.error("internal_error", error=str(e))
    return jsonify({"error": "internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info("app_starting", port=port)
    app.run(host='0.0.0.0', port=port)
