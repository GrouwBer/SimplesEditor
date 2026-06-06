from flask import Flask, jsonify, request
import os
from logging_config import setup_logging, get_logger

# Inicializar logs estruturados
setup_logging()
logger = get_logger(__name__)

app = Flask(__name__)


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


@app.errorhandler(500)
def internal_error(e):
    logger.error("internal_error", error=str(e))
    return jsonify({"error": "internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info("app_starting", port=port)
    app.run(host='0.0.0.0', port=port)
