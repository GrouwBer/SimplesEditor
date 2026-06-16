"""
Executor de codigo no sandbox Docker com timeout.

Gerencia o ciclo de vida de execucao de codigo compilado dentro do
container sandbox, aplicando:
- Timeout wall-clock de 10s (configuravel via EXEC_TIMEOUT_S)
- Hard limits de recursos (CPU, memoria, PIDs, read-only, etc.)
- Metricas Prometheus
- Log estruturado
"""

import os
import signal
import threading
import time
from typing import NamedTuple

import docker
from docker.errors import DockerException, ContainerError, APIError

from app import (
    EXECUTIONS_TOTAL,
    EXECUTION_DURATION,
    ACTIVE_CONTAINERS,
    logger,
)
from sandbox_config import APP_CONFIG, get_sandbox_run_kwargs


class ExecResult(NamedTuple):
    """Resultado de uma execucao no sandbox."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration_s: float


class ExecutorError(Exception):
    """Erro durante a execucao no sandbox."""

    pass


def _get_docker_client() -> docker.DockerClient:
    """Retorna um cliente Docker configurado."""
    try:
        return docker.from_env()
    except DockerException as e:
        logger.error("docker_client_error", error=str(e))
        raise ExecutorError(f"Falha ao conectar ao Docker: {e}")


def run_code_in_sandbox(
    binary_path: str,
    stdin: str = "",
    timeout: int | None = None,
) -> ExecResult:
    """
    Executa um binario compilado dentro do sandbox Docker com timeout.

    Args:
        binary_path: Caminho absoluto para o binario dentro do container.
        stdin: Texto a ser enviado para o stdin do processo.
        timeout: Timeout wall-clock em segundos.
                 Se None, usa APP_CONFIG["timeout"].

    Returns:
        ExecResult com stdout, stderr, exit_code, timed_out e duration_s.

    Raises:
        ExecutorError: Se falhar ao criar/executar o container.
    """
    if timeout is None:
        timeout = APP_CONFIG["timeout"]

    # O stop_timeout do container precisa ser maior que o exec timeout
    # para dar tempo do SIGTERM ser processado antes do SIGKILL
    stop_timeout = min(timeout + 2, 14)

    client = _get_docker_client()
    run_kwargs = get_sandbox_run_kwargs()
    run_kwargs["stop_timeout"] = stop_timeout

    start_time = time.monotonic()
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code = -1

    container = None
    try:
        logger.info(
            "sandbox_exec_start",
            binary=binary_path,
            timeout=timeout,
        )
        ACTIVE_CONTAINERS.inc()

        # Cria e inicia o container
        container = client.containers.run(
            image=APP_CONFIG["sandbox_image"],
            command=["/sandbox/prog"],
            detach=True,
            **run_kwargs,
        )

        # Monitora o container com timeout
        exit_code = _wait_container(container, timeout)

        if exit_code is None:
            # Timeout: mata o container
            timed_out = True
            logger.warning("sandbox_exec_timeout", timeout=timeout)
            _kill_container(container)

            # Recupera logs parciais antes de destruir
            try:
                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                pass

            EXECUTIONS_TOTAL.labels(status="timeout").inc()
            exit_code = -1
        else:
            # Captura logs
            try:
                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                pass

            EXECUTIONS_TOTAL.labels(
                status="success" if exit_code == 0 else "error"
            ).inc()

        duration = time.monotonic() - start_time
        EXECUTION_DURATION.observe(duration)

        logger.info(
            "sandbox_exec_end",
            exit_code=exit_code,
            duration_s=round(duration, 3),
            timed_out=timed_out,
        )

        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
            duration_s=duration,
        )

    except DockerException as e:
        EXECUTIONS_TOTAL.labels(status="error").inc()
        logger.error("sandbox_exec_error", error=str(e))
        raise ExecutorError(f"Erro no sandbox Docker: {e}")

    finally:
        if container is not None:
            _remove_container(container)
        ACTIVE_CONTAINERS.dec()


def _wait_container(container, timeout: int) -> int | None:
    """
    Aguarda o container terminar ou o timeout expirar.

    Returns:
        Exit code (int) ou None se timeout.
    """
    # O container ja foi iniciado com detach=True
    # Usamos um loop de polling com verificacao de timeout
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        container.reload()
        status = container.status
        if status == "exited":
            return container.attrs["State"]["ExitCode"]
        time.sleep(0.1)

    return None  # Timeout


def _kill_container(container):
    """Mata o container com SIGTERM e depois SIGKILL se necessario."""
    try:
        container.stop(timeout=10)
    except Exception:
        try:
            container.kill()
        except Exception:
            pass


def _remove_container(container):
    """Remove o container com forc-a."""
    try:
        container.remove(force=True)
    except Exception:
        pass
