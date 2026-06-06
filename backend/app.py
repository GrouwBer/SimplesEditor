from flask import Flask, jsonify, request, abort
import os
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

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


@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
