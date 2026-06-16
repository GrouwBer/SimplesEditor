from flask import Flask, jsonify, request, abort
import os
import subprocess
import tempfile
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
    RF05 — Invoca simplesc e retorna NASM ou erros de compilacao.

    Espera JSON: {"code": "<codigo SIMPLES>"}
    Retorna:
      - 200: {"status": "ok", "nasm": "<codigo NASM>"}
      - 422: {"status": "error", "errors": [{"line": N, "column": M, "message": "..."}]}
      - 400: {"status": "error", "errors": [{"message": "..."}]}
      - 500: {"status": "error", "errors": [{"message": "internal compilation error"}]}
    """
    body = request.get_json(silent=True) or {}
    code = body.get('code', '').strip()

    if not code:
        return jsonify({
            "status": "error",
            "errors": [{"message": "codigo fonte vazio"}]
        }), 400

    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.sim', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ['simplesc', tmp_path],
            capture_output=True,
            text=True,
            timeout=int(os.environ.get('COMPILE_TIMEOUT_S', '15')),
        )

        os.unlink(tmp_path)

    except FileNotFoundError:
        logger.error("compile_error", detail="simplesc not found")
        return jsonify({
            "status": "error",
            "errors": [{"message": "simplesc nao encontrado no container"}]
        }), 500

    except subprocess.TimeoutExpired:
        os.unlink(tmp_path)
        COMPILATIONS_TOTAL.labels(status='timeout').inc()
        return jsonify({
            "status": "error",
            "errors": [{"message": "compilacao excedeu o tempo limite"}]
        }), 422

    if result.returncode == 0:
        COMPILATIONS_TOTAL.labels(status='success').inc()
        logger.info("compile_success", code_length=len(code))
        return jsonify({
            "status": "ok",
            "nasm": result.stdout.strip()
        })
    else:
        COMPILATIONS_TOTAL.labels(status='error').inc()
        errors = _parse_compile_errors(result.stderr)
        logger.info("compile_failed", error_count=len(errors))
        return jsonify({
            "status": "error",
            "errors": errors
        }), 422


def _parse_compile_errors(stderr: str) -> list:
    """
    RF08 — Converte stderr do simplesc em lista de {line, column, message}.

    Formato esperado do simplesc:
        <arquivo>:<linha>:<coluna>: error: <mensagem>
        <arquivo>:<linha>:<coluna>: warning: <mensagem>
        <arquivo>:<linha>: error: <mensagem>
        <mensagem livre>

    Fallback: se nao bater o padrao, retorna a saida completa como
    um unico erro sem line/column.
    """
    import re

    errors = []
    lines = stderr.strip().split('\n') if stderr.strip() else []

    # Ex: /tmp/foo.sim:3:12: error: token inesperado
    pattern = re.compile(
        r'^(?P<file>[^:]+):(?P<line>\d+):(?:(?P<column>\d+):)?\s*(?P<kind>error|warning):\s*(?P<message>.+)$'
    )

    for line in lines:
        m = pattern.match(line.strip())
        if m:
            err = {
                "line": int(m.group('line')),
                "message": m.group('message').strip()
            }
            if m.group('column'):
                err["column"] = int(m.group('column'))
            if m.group('kind') == 'warning':
                err["kind"] = "warning"
            else:
                err["kind"] = "error"
            errors.append(err)
        elif line.strip():
            errors.append({"message": line.strip()})

    if not errors:
        errors.append({
            "message": stderr.strip() or "erro de compilacao desconhecido"
        })

    return errors


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
