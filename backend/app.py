from flask import Flask, jsonify, request
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from logging_config import setup_logging, get_logger

# Inicializar logs estruturados
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)

# Metricas Prometheus
EXECUTIONS_TOTAL = Counter(
    'simples_executions_total',
    'Total de execucoes de codigo',
    ['status']
)

EXECUTION_DURATION = Histogram(
    'simples_execution_duration_seconds',
    'Duracao das execucoes em segundos',
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

COMPILATIONS_TOTAL = Counter(
    'simples_compilations_total',
    'Total de compilacoes',
    ['status']
)

ACTIVE_CONTAINERS = Counter(
    'simples_containers_total',
    'Total de containers criados',
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


@app.route('/api/health')
def health():
    logger.debug("health_check")
    return jsonify({"status": "ok"})


@app.route('/metrics')
def metrics():
    """Endpoint Prometheus — bloqueado externamente pelo nginx."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.errorhandler(500)
def internal_error(e):
    logger.error("internal_error", error=str(e))
    return jsonify({"error": "internal server error"}), 500


if __name__ == '__main__':
    logger.info("app_starting", port=os.environ.get('PORT', 5000))
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
