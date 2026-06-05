"""
Configuracao de hard limits do container sandbox.

Define os limites de seguranca aplicados a cada execucao de codigo
de aluno via Docker SDK (docker-py).
"""

import os

# ============================================================
# Hard limits do container
# ============================================================

SANDBOX_CONFIG = {
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

    # ============================================================
    # Docker container limits
    # ============================================================

    # Memoria maxima (RAM)
    "mem_limit": "64m",

    # CPU quota (0.5 = 50% de um core)
    "cpu_quota": 50000,     # microsegundos por periodo
    "cpu_period": 100000,   # periodo padrao (100ms)

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

    # Bloqueio total de dispositivos
    "device_read_bps": [],
    "device_write_bps": [],
}


def get_sandbox_run_kwargs():
    """
    Retorna os kwargs para docker-py's client.containers.run()
    com todos os hard limits aplicados.
    """
    return {
        "mem_limit": SANDBOX_CONFIG["mem_limit"],
        "cpu_quota": SANDBOX_CONFIG["cpu_quota"],
        "cpu_period": SANDBOX_CONFIG["cpu_period"],
        "stop_timeout": SANDBOX_CONFIG["stop_timeout"],
        "pids_limit": SANDBOX_CONFIG["pids_limit"],
        "network_disabled": SANDBOX_CONFIG["network_disabled"],
        "read_only": SANDBOX_CONFIG["read_only"],
        "tmpfs": SANDBOX_CONFIG["tmpfs"],
        "cap_drop": SANDBOX_CONFIG["cap_drop"],
        "security_opt": SANDBOX_CONFIG["security_opt"],
    }
