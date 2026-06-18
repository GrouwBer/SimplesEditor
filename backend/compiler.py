"""
Modulo de compilacao do pipeline SIMPLES → NASM → ELF.

Gerencia o pipeline de compilacao:
  1. Invoca simplesc (SIMPLES → NASM)
  2. Invoca nasm (NASM → .o)
  3. Invoca ld (.o → ELF i686)

Cada etapa e isolada e tratada com timeout.
"""

import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import NamedTuple

from logging_config import get_logger
from sandbox_config import APP_CONFIG


logger = get_logger(__name__)


class CompilePhaseResult(NamedTuple):
    """Resultado de uma fase da compilacao."""

    success: bool
    output: str
    error: str
    duration_s: float


class CompileResult(NamedTuple):
    """Resultado completo da compilacao."""

    success: bool
    nasm_output: str | None
    binary_path: str | None
    errors: list[dict]
    duration_s: float
    phases: dict[str, CompilePhaseResult]


# Caminhos dos executaveis
SIMPLESC_PATH = os.environ.get(
    "SIMPLESC_PATH",
    "/usr/local/bin/simplesc",
)
NASM_PATH = os.environ.get("NASM_PATH", "nasm")
LD_PATH = os.environ.get(
    "LD_PATH",
    "i686-linux-gnu-ld",
)

# Diretorio temporario para artefatos de compilacao
COMPILE_TMP = os.environ.get("COMPILE_TMP", "/tmp/simples")


def _ensure_tmp_dir():
    """Garante que o diretorio temporario existe."""
    Path(COMPILE_TMP).mkdir(parents=True, exist_ok=True)


def _run_command(
    cmd: list[str],
    stdin: str = "",
    timeout: int | None = None,
    cwd: str | None = None,
) -> CompilePhaseResult:
    """
    Executa um comando do pipeline com timeout.

    Args:
        cmd: Comando e argumentos.
        stdin: Entrada padrao (stdin).
        timeout: Timeout em segundos. Se None, usa compile_timeout do config.
        cwd: Diretorio de trabalho.

    Returns:
        CompilePhaseResult com output, error e duracao.
    """
    if timeout is None:
        timeout = APP_CONFIG["compile_timeout"]

    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            input=stdin.encode("utf-8") if stdin else None,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
        )
        duration = time.monotonic() - start

        return CompilePhaseResult(
            success=result.returncode == 0,
            output=result.stdout.decode("utf-8", errors="replace"),
            error=result.stderr.decode("utf-8", errors="replace"),
            duration_s=duration,
        )

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return CompilePhaseResult(
            success=False,
            output="",
            error=f"Comando excedeu o timeout de {timeout}s",
            duration_s=duration,
        )

    except FileNotFoundError as e:
        duration = time.monotonic() - start
        return CompilePhaseResult(
            success=False,
            output="",
            error=f"Comando nao encontrado: {e}",
            duration_s=duration,
        )

    except Exception as e:
        duration = time.monotonic() - start
        return CompilePhaseResult(
            success=False,
            output="",
            error=f"Erro ao executar comando: {e}",
            duration_s=duration,
        )


def _parse_simplesc_errors(stderr: str) -> list[dict]:
    """
    Extrai erros com linha/coluna da saida do simplesc.

    Formato esperado: "erro na linha L, coluna C: mensagem"
    ou padrao similar.

    Returns:
        Lista de dicts com keys: line, column, message.
    """

    errors = []
    # Tenta corresponder padroes como "linha 5" ou "line 5"
    patterns = [
        r"(?:linha|line)\s*(\d+)(?:,\s*(?:coluna|column|col)\s*(\d+))?\s*:\s*(.+)",
        r":(\d+):(\d+):\s*(.+)",  # formato GCC-like
        r"\[linha\s*(\d+)(?:,\s*coluna\s*(\d+))?\]\s*(.+)",
    ]

    for line in stderr.split("\n"):
        line = line.strip()
        if not line:
            continue
        matched = False
        for pattern in patterns:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                groups = m.groups()
                errors.append({
                    "line": int(groups[0]) if groups[0] else 0,
                    "column": int(groups[1]) if groups[1] else 0,
                    "message": groups[2] if len(groups) > 2 else line,
                })
                matched = True
                break
        if not matched:
            # Se nao corresponder a nenhum padrao, adiciona como erro generico
            if "error" in line.lower() or "erro" in line.lower():
                errors.append({
                    "line": 0,
                    "column": 0,
                    "message": line,
                })

    return errors


def compile_source(source_code: str) -> CompileResult:
    """
    Compila codigo fonte SIMPLES seguindo o pipeline completo.

    Pipeline:
      1. Salva codigo fonte em .simples
      2. simplesc → .asm (NASM)
      3. nasm -f elf32 → .o
      4. i686-linux-gnu-ld → binario i686 ELF

    Args:
        source_code: Codigo fonte SIMPLES.

    Returns:
        CompileResult com resultados de cada fase.
    """
    _ensure_tmp_dir()
    start = time.monotonic()
    phases: dict[str, CompilePhaseResult] = {}
    errors: list[dict] = []

    # Import lazy para evitar circular import com app.py
    from app import COMPILATIONS_TOTAL

    # Gera ID unico para este ciclo de compilacao
    compile_id = uuid.uuid4().hex[:8]
    work_dir = Path(COMPILE_TMP) / compile_id
    work_dir.mkdir(parents=True, exist_ok=True)

    source_path = work_dir / "source.simples"
    asm_path = work_dir / "output.asm"
    obj_path = work_dir / "output.o"
    binary_path = work_dir / "prog"

    try:
        # --- Fase 0: Salva codigo fonte ---
        source_path.write_text(source_code, encoding="utf-8")

        # --- Fase 1: SIMPLES → NASM (simplesc) ---
        phase1 = _run_command(
            [SIMPLESC_PATH, str(source_path)],
            timeout=APP_CONFIG["compile_timeout"],
            cwd=str(work_dir),
        )
        phases["simplesc"] = phase1

        if not phase1.success:
            errors = _parse_simplesc_errors(phase1.error)
            # Pega output NASM mesmo com erros parciais
            nasm_output = phase1.output
            COMPILATIONS_TOTAL.labels(status="error").inc()
            duration = time.monotonic() - start
            return CompileResult(
                success=False,
                nasm_output=nasm_output or None,
                binary_path=None,
                errors=errors,
                duration_s=duration,
                phases=phases,
            )

        nasm_output = phase1.output

        # Salva output NASM em arquivo
        asm_path.write_text(phase1.output, encoding="utf-8")

        # --- Fase 2: NASM → .o (nasm) ---
        phase2 = _run_command(
            [NASM_PATH, "-f", "elf32", str(asm_path), "-o", str(obj_path)],
            timeout=APP_CONFIG["compile_timeout"],
            cwd=str(work_dir),
        )
        phases["nasm"] = phase2

        if not phase2.success:
            COMPILATIONS_TOTAL.labels(status="error").inc()
            duration = time.monotonic() - start
            return CompileResult(
                success=False,
                nasm_output=nasm_output,
                binary_path=None,
                errors=[{"line": 0, "column": 0, "message": phase2.error}],
                duration_s=duration,
                phases=phases,
            )

        # --- Fase 3: .o → ELF (ld) ---
        phase3 = _run_command(
            [LD_PATH, str(obj_path), "-o", str(binary_path)],
            timeout=APP_CONFIG["compile_timeout"],
            cwd=str(work_dir),
        )
        phases["ld"] = phase3

        if not phase3.success:
            COMPILATIONS_TOTAL.labels(status="error").inc()
            duration = time.monotonic() - start
            return CompileResult(
                success=False,
                nasm_output=nasm_output,
                binary_path=None,
                errors=[{"line": 0, "column": 0, "message": phase3.error}],
                duration_s=duration,
                phases=phases,
            )

        # --- Sucesso ---
        COMPILATIONS_TOTAL.labels(status="success").inc()
        duration = time.monotonic() - start

        logger.info(
            "compile_success",
            compile_id=compile_id,
            duration_s=round(duration, 3),
        )

        return CompileResult(
            success=True,
            nasm_output=nasm_output,
            binary_path=str(binary_path),
            errors=[],
            duration_s=duration,
            phases=phases,
        )

    except Exception as e:
        duration = time.monotonic() - start
        COMPILATIONS_TOTAL.labels(status="error").inc()
        logger.error("compile_error", error=str(e))
        return CompileResult(
            success=False,
            nasm_output=None,
            binary_path=None,
            errors=[{"line": 0, "column": 0, "message": str(e)}],
            duration_s=duration,
            phases=phases,
        )

    finally:
        # Limpa artefatos temporarios (opcional: mantem para debug)
        if not os.environ.get("KEEP_COMPILE_ARTIFACTS"):
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass
