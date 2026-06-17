import structlog
import logging
import os
import sys


def setup_logging():
    """Configura logs estruturados em JSON via structlog."""

    # Configurar o processador JSON para saida estruturada
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configurar o logger raiz para nivel configurado
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=os.environ.get("LOG_LEVEL", "INFO"),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Retorna um logger estruturado.

    Se name for None, usa __name__ do frame chamador.
    """
    if name is None:
        import inspect
        frame = inspect.currentframe()
        try:
            caller = frame.f_back
            name = caller.f_globals.get("__name__", "root")
        finally:
            del frame
    return structlog.get_logger(name)
