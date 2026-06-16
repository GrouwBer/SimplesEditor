"""
Enforcement de timeout para compilacao e execucao.

Garante que:
  - Compilacao (simplesc, nasm, ld) e interrompida apos 15s (RF15)
  - Execucao e interrompida apos 10s (RF14)
  - Loop infinito e interrompido em ~11s

Os timeouts sao configurados em sandbox_config.APP_CONFIG:
  - compile_timeout: 15s (padrao)
  - timeout: 10s (padrao de execucao)
"""

import signal
import subprocess
import sys
import threading
import time
from typing import IO, Any

from sandbox_config import APP_CONFIG


class TimeoutError(subprocess.TimeoutExpired):
    """Excecao lancada quando um comando excede o tempo limite."""

    def __init__(self, cmd: list[str], timeout: float, output: str = ""):
        super().__init__(cmd, timeout, output)
        self.timeout_s = timeout
        self.cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd


def run_with_timeout(
    cmd: list[str],
    timeout: int | None = None,
    stdin: str = "",
    capture_output: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """
    Executa um comando com timeout obrigatorio.

    Args:
        cmd: Comando e argumentos.
        timeout: Timeout em segundos. Se None, usa compile_timeout do config.
        stdin: Entrada padrao.
        capture_output: Capturar stdout/stderr.
        **kwargs: Argumentos adicionais para subprocess.run.

    Returns:
        subprocess.CompletedProcess.

    Raises:
        TimeoutError: Se o comando exceder o timeout.
    """
    if timeout is None:
        timeout = APP_CONFIG["compile_timeout"]

    try:
        result = subprocess.run(
            cmd,
            input=stdin.encode("utf-8") if stdin else None,
            capture_output=capture_output,
            timeout=timeout,
            **kwargs,
        )
        return result

    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = ""
        if hasattr(cmd, 'stdout'):
            stdout = cmd.stdout
        if hasattr(cmd, 'stderr'):
            stderr = cmd.stderr

        raise TimeoutError(
            cmd=cmd,
            timeout=timeout,
            output=f"Comando excedeu o timeout de {timeout}s",
        )


def get_compile_timeout() -> int:
    """Retorna o timeout de compilacao configurado."""
    return APP_CONFIG["compile_timeout"]


def get_exec_timeout() -> int:
    """Retorna o timeout de execucao configurado."""
    return APP_CONFIG["timeout"]


def format_timeout_error(timeout_s: int, phase: str = "compilacao") -> str:
    """Retorna mensagem de erro padronizada para timeout."""
    return (
        f"[TIMEOUT] {phase.capitalize()} excedeu o limite de {timeout_s}s. "
        f"Verifique se o codigo contem loops infinitos ou operacoes muito longas."
    )
