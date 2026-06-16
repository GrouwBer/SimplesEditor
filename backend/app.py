from flask import Flask, jsonify, request, abort
import os
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from logging_config import setup_logging, get_logger

# Inicializar logs estruturados
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)

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


@app.route('/api/compile', methods=['POST'])
def compile_code():
    """
    Endpoint de compilacao SIMPLES → NASM → ELF.

    Recebe codigo fonte SIMPLES, executa o pipeline de compilacao
    e retorna o NASM gerado ou erros com linha/coluna.

    Request body (JSON):
        { "code": "programa ..." }

    Resposta (200):
        { "success": true, "nasm": "...", "binary_path": "...", ... }

    Resposta (200 com erro de compilacao):
        { "success": false, "errors": [...], "nasm": "..." }

    Resposta (400):
        { "error": "campo 'code' obrigatorio" }
    """
    from compiler import compile_source

    data = request.get_json(silent=True)
    if not data or "code" not in data:
        return jsonify({"error": "campo 'code' obrigatorio"}), 400

    source_code = data["code"]

    # Valida tamanho maximo
    max_kb = __import__('sandbox_config').APP_CONFIG["max_code_kb"]
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
