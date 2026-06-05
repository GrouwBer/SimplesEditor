from flask import Flask, jsonify
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Metricas Prometheus
EXECUTIONS_TOTAL = Counter(
    'simples_executions_total',
    'Total de execucoes de codigo',
    ['status']  # success, error, timeout
)

EXECUTION_DURATION = Histogram(
    'simples_execution_duration_seconds',
    'Duracao das execucoes em segundos',
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

COMPILATIONS_TOTAL = Counter(
    'simples_compilations_total',
    'Total de compilacoes',
    ['status']  # success, error
)

ACTIVE_CONTAINERS = Counter(
    'simples_containers_total',
    'Total de containers criados (aproximacao de ativos)',
)


@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/metrics')
def metrics():
    """Endpoint Prometheus — bloqueado externamente pelo nginx."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
