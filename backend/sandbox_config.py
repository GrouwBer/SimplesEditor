"""
Configuracao de hard limits do container sandbox.

Define os limites de seguranca aplicados a cada execucao de codigo
de aluno via Docker SDK (docker-py).
"""

import os
from typing import Any

# ============================================================
# Configuracoes da aplicacao
# ============================================================

APP_CONFIG = {
    # Tempo maximo de execucao (wall-clock)
    "timeout": int(os.environ.get("EXEC_TIMEOUT_S", "10")),

    # Tempo maximo de compilacao
    "compile_timeout": int(os.environ.get("COMPILE_TIMEOUT_S", "15")),

    # Tamanho maximo do codigo fonte (KB)
    "max_code_kb": int(os.environ.get("MAX_CODE_KB", "64")),

    # Rate limit: execucoes por minuto por usuario
    "runs_per_minute": int(os.environ.get("RUNS_PER_MINUTE", "30")),

    # Nome da imagem do sandbox
    "sandbox_image": os.environ.get("SANDBOX_IMAGE", "simples-runner:latest"),
}

# ============================================================
# Docker container hard limits
# ============================================================

DOCKER_HARD_LIMITS = {
    # Memoria maxima (RAM) — parametrizavel via env var
    "mem_limit": os.environ.get("SANDBOX_MEM_LIMIT", "64m"),

    # CPU quota (0.5 = 50% de um core) — parametrizavel via env var
    "cpu_quota": int(os.environ.get("SANDBOX_CPU_QUOTA", "50000")),
    "cpu_period": int(os.environ.get("SANDBOX_CPU_PERIOD", "100000")),

    # Timeout do stop (SIGTERM → SIGKILL)
    "stop_timeout": 12,     # segundos

    # PIDs maximo (previne fork bomb)
    "pids_limit": 64,

    # Bloqueio de rede
    "network_disabled": True,

    # Filesystem read-only (exceto /tmp)
    "read_only": True,

    # tmpfs para /tmp (volatil, isolado)
    "tmpfs": {"/tmp": "size=16m,noexec,nosuid"},

    # Capacidades removidas
    "cap_drop": ["ALL"],

    # Seguranca adicional
    "security_opt": ["no-new-privileges"],
}

# Chaves do DOCKER_HARD_LIMITS que sao repassadas para docker-py
_DOCKER_KWARGS_KEYS = [
    "mem_limit",
    "cpu_quota",
    "cpu_period",
    "pids_limit",
    "network_disabled",
    "read_only",
    "tmpfs",
    "cap_drop",
    "security_opt",
]

# Compatibilidade: SANDBOX_CONFIG unificado (APP_CONFIG + DOCKER_HARD_LIMITS)
SANDBOX_CONFIG = {**APP_CONFIG, **DOCKER_HARD_LIMITS}


def get_sandbox_run_kwargs() -> dict[str, Any]:
    """
    Retorna os kwargs para docker-py's client.containers.run()
    com todos os hard limits aplicados.
    """
    return {key: DOCKER_HARD_LIMITS[key] for key in _DOCKER_KWARGS_KEYS}
