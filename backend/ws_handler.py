"""
WebSocket handler para /ws/run.

Gerencia o ciclo completo: compile → run → output streaming → stop.

Protocolo de mensagens (alinhado com frontend useExecution.ts):
...
"""

import json
import os
import re

import signal
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from flask import Flask
from flask_sock import Sock, Server

from logging_config import get_logger

from sandbox_config import APP_CONFIG, get_sandbox_run_kwargs


# Logger obtido via funcao para evitar imports circulares
logger = get_logger(__name__)

# Margem de espera adicional apos o timeout para aguardar o container
_CONTAINER_WAIT_GRACE_S = 5

# Diretorio temporario para artefatos
COMPILE_TMP = os.environ.get("COMPILE_TMP", "/tmp/simples")
SIMPLESC_PATH = os.environ.get("SIMPLESC_PATH", "/usr/local/bin/simplesc")
NASM_PATH = os.environ.get("NASM_PATH", "nasm")
LD_PATH = os.environ.get("LD_PATH", "i686-linux-gnu-ld")


class WsRunHandler:
    """
    Gerencia uma conexao WebSocket para execucao de codigo.
    Uma instancia por conexao.
    """

    def __init__(self, ws: Server):
        self.ws = ws
        self._process: subprocess.Popen | None = None
        self._container_id: str | None = None
        self._stdin_socket = None  # socket do stdin do container Docker
        self._running = False
        self._timed_out = False
        self._exit_code: int | None = None
        self._lock = threading.Lock()

    # ---------------------------------------------------------------
    # API publica — chamada pelo loop de mensagens
    # ---------------------------------------------------------------

    def handle_compile_and_run(self, code: str):
        """Compila e executa o codigo SIMPLES."""
        threading.Thread(
            target=self._run_pipeline,
            args=(code,),
            daemon=True,
        ).start()

    def handle_stdin(self, data: str):
        """Envia dados para o stdin do processo em execucao."""
        with self._lock:
            # Docker sandbox path (stdin via socket)
            if self._stdin_socket:
                try:
                    import docker
                    sock = self._stdin_socket
                    sock.send(data.encode("utf-8"))
                except Exception:
                    pass
            # Subprocess path (fallback)
            elif self._process and self._process.stdin:
                try:
                    self._process.stdin.write(data.encode("utf-8"))
                    self._process.stdin.flush()
                except Exception:
                    pass

    def handle_stop(self):
        """Para a execucao (SIGTERM → SIGKILL)."""
        with self._lock:
            if self._process:
                try:
                    self._process.send_signal(signal.SIGTERM)
                    # Se nao morrer em 1s, SIGKILL

                    def force_kill():
                        time.sleep(1)
                        try:
                            self._process.kill()
                        except Exception:
                            pass
                    threading.Thread(target=force_kill, daemon=True).start()
                except Exception:
                    pass
            elif self._container_id:
                try:
                    import docker
                    client = docker.from_env()
                    try:
                        container = client.containers.get(self._container_id)
                        container.stop(timeout=10)
                    except Exception:
                        pass
                except Exception:
                    pass

    # ---------------------------------------------------------------
    # Pipeline: compile → run
    # ---------------------------------------------------------------

    def _send(self, msg: dict[str, Any]):
        """Envia mensagem JSON para o cliente WebSocket."""
        try:
            self.ws.send(json.dumps(msg))
        except Exception as e:
            logger.error("ws_send_error", error=str(e))

    def _run_pipeline(self, code: str):
        """Pipeline completo: compile → run → output."""
        start_time = time.monotonic()

        try:
            self._send({"type": "compile_started"})

            # --- Fase 1: Compilar ---
            result = self._compile(code)
            if result is None:
                return  # Erro ja enviado

            nasm_code, binary_path = result
            self._send({"type": "asm_generated", "asm": nasm_code})

            # --- Fase 2: Executar ---
            self._send({"type": "exec_started"})
            self._run_binary(binary_path)

            # --- Fase 3: Resultado ---
            duration_s = time.monotonic() - start_time
            duration_ms = int(duration_s * 1000)

            if self._timed_out:
                self._send({
                    "type": "timeout",
                    "limit_s": APP_CONFIG["timeout"],
                })
                from app import EXECUTIONS_TOTAL
                EXECUTIONS_TOTAL.labels(status="timeout").inc()
            else:
                exit_code = self._exit_code if self._exit_code is not None else -1
                self._send({
                    "type": "exit",
                    "exit_code": exit_code,
                    "duration_ms": duration_ms,
                })
                from app import EXECUTIONS_TOTAL
                EXECUTIONS_TOTAL.labels(
                    status="success" if exit_code == 0 else "error"
                ).inc()

            from app import EXECUTION_DURATION
            EXECUTION_DURATION.observe(duration_s)

        except Exception as e:
            logger.error("pipeline_error", error=str(e))
            self._send({"type": "internal_error", "message": str(e)})

    # ---------------------------------------------------------------
    # Compilacao
    # ---------------------------------------------------------------

    def _compile(self, code: str) -> tuple[str, str] | None:
        """
        Compila codigo SIMPLES → NASM → ELF.
        Retorna (nasm_code, binary_path) ou None em caso de erro.
        """
        compile_id = uuid.uuid4().hex[:8]
        work_dir = Path(COMPILE_TMP) / compile_id
        work_dir.mkdir(parents=True, exist_ok=True)

        source_path = work_dir / "source.simples"
        asm_path = work_dir / "output.asm"
        obj_path = work_dir / "output.o"
        binary_path = work_dir / "prog"

        try:
            # Salva codigo fonte
            source_path.write_text(code, encoding="utf-8")

            # --- Fase 1: SIMPLES → NASM ---
            phase1 = self._run_cmd(
                [SIMPLESC_PATH, str(source_path), "-o", str(asm_path)],
                timeout=APP_CONFIG["compile_timeout"],
            )
            if phase1 is None or phase1["returncode"] != 0:
                stderr = phase1["stderr"] if phase1 else "erro ao executar simplesc"
                self._send({
                    "type": "compile_error",
                    "line": self._extract_line(stderr, 0),
                    "column": self._extract_column(stderr, 0),
                    "message": stderr[:500],
                })
                from app import COMPILATIONS_TOTAL
                COMPILATIONS_TOTAL.labels(status="error").inc()
                return None

            # Le NASM do arquivo gerado pelo compilador
            nasm_code = asm_path.read_text(encoding="utf-8")

            # --- Fase 2: NASM → .o ---
            phase2 = self._run_cmd(
                [NASM_PATH, "-f", "elf32", str(asm_path), "-o", str(obj_path)],
                timeout=APP_CONFIG["compile_timeout"],
            )
            if phase2 is None or phase2["returncode"] != 0:
                stderr = phase2["stderr"] if phase2 else "erro no nasm"
                self._send({
                    "type": "assemble_error",
                    "message": stderr[:500],
                })
                from app import COMPILATIONS_TOTAL
                COMPILATIONS_TOTAL.labels(status="error").inc()
                return None

            # --- Fase 3: .o → ELF ---
            phase3 = self._run_cmd(
                [LD_PATH, str(obj_path), "-o", str(binary_path)],
                timeout=APP_CONFIG["compile_timeout"],
            )
            if phase3 is None or phase3["returncode"] != 0:
                stderr = phase3["stderr"] if phase3 else "erro no ld"
                self._send({
                    "type": "link_error",
                    "message": stderr[:500],
                })
                from app import COMPILATIONS_TOTAL
                COMPILATIONS_TOTAL.labels(status="error").inc()
                return None

            from app import COMPILATIONS_TOTAL
            COMPILATIONS_TOTAL.labels(status="success").inc()
            return nasm_code, str(binary_path)

        except Exception as e:
            logger.error("compile_error", error=str(e))
            self._send({"type": "internal_error", "message": str(e)})
            return None

    def _run_cmd(
        self, cmd: list[str], timeout: int
    ) -> dict[str, Any] | None:
        """Executa um comando e retorna resultado."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8", errors="replace"),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"timeout: comando excedeu {timeout}s",
            }
        except FileNotFoundError:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"comando nao encontrado: {cmd[0]}",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }

    # ---------------------------------------------------------------
    # Execucao no sandbox
    # ---------------------------------------------------------------

    def _run_binary(self, binary_path: str):
        """
        Executa o binario no sandbox Docker com streaming de I/O e stdin interativo.
        """
        self._running = True
        self._timed_out = False
        self._exit_code = None
        self._stdin_socket = None

        try:
            import docker
            client = docker.from_env()
            from app import ACTIVE_CONTAINERS
            ACTIVE_CONTAINERS.inc()

            # Cria bind mount para o binario
            binary_dir = os.path.dirname(binary_path)
            binary_name = os.path.basename(binary_path)
            host_binary_dir = os.path.normpath(binary_dir)

            volumes = {
                host_binary_dir: {
                    "bind": "/sandbox",
                    "mode": "ro",
                }
            }

            run_kwargs = get_sandbox_run_kwargs()
            run_kwargs["volumes"] = volumes
            run_kwargs["detach"] = True
            run_kwargs["stdin_open"] = True  # Mantem stdin aberto para leia

            container = client.containers.run(
                image=APP_CONFIG["sandbox_image"],
                command=["/sandbox/" + binary_name],
                **run_kwargs,
            )
            self._container_id = container.id

            # Conecta socket de stdin para input interativo (leia)
            try:
                sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
                self._stdin_socket = sock
            except Exception:
                pass

            # Streaming de logs em tempo real (stdout/stderr)
            try:
                for line in container.logs(stdout=True, stderr=True, stream=True, follow=True):
                    if isinstance(line, bytes):
                        text = line.decode("utf-8", errors="replace")
                        self._send({"type": "stdout", "data": text})
            except Exception:
                pass

            # Aguarda e pega exit code
            exit_result = container.wait(timeout=APP_CONFIG["timeout"] + _CONTAINER_WAIT_GRACE_S)
            exit_code = exit_result.get("StatusCode", -1)
            self._exit_code = exit_code

        except docker.errors.DockerException as e:
            self._exit_code = -1
            self._send({"type": "stderr", "data": f"Erro Docker: {e}"})

        except Exception as e:
            self._exit_code = -1
            self._send({"type": "internal_error", "message": str(e)})

        finally:
            self._running = False
            # Fecha socket de stdin
            if self._stdin_socket:
                try:
                    self._stdin_socket.close()
                except Exception:
                    pass
                self._stdin_socket = None
            from app import ACTIVE_CONTAINERS
            ACTIVE_CONTAINERS.dec()
            # Remove container
            try:
                import docker
                client = docker.from_env()
                try:
                    c = client.containers.get(self._container_id)
                    c.remove(force=True)
                except Exception:
                    pass
            except Exception:
                pass

    # ---------------------------------------------------------------
    # Utilitarios
    # ---------------------------------------------------------------

    @staticmethod
    def _extract_line(stderr: str, default: int = 0) -> int:
        """Extrai numero da linha de mensagem de erro (formato phase:line:col: msg)."""
        # Formato do professor: lexer:5:12: mensagem
        m = re.search(r":(\d+):", stderr)
        if m:
            return int(m.group(1))
        m = re.search(r"(?:linha|line)\s*(\d+)", stderr, re.IGNORECASE)
        return int(m.group(1)) if m else default

    @staticmethod
    def _extract_column(stderr: str, default: int = 0) -> int:
        """Extrai numero da coluna de mensagem de erro (formato phase:line:col: msg)."""
        m = re.search(r":\d+:(\d+):", stderr)
        if m:
            return int(m.group(1))
        m = re.search(r"(?:coluna|column|col)\s*(\d+)", stderr, re.IGNORECASE)
        return int(m.group(1)) if m else default


# ============================================================
# Registro do WebSocket
# ============================================================

def register_websocket(app: Flask):
    """Registra o endpoint WebSocket /ws/run no app Flask."""
    sock = Sock(app)

    @sock.route("/ws/run")
    def ws_run(ws: Server):
        """Endpoint WebSocket para execucao de codigo."""
        handler = WsRunHandler(ws)
        logger.info("ws_connected", path="/ws/run")

        try:
            while True:
                message = ws.receive()
                if message is None:
                    break

                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "compile_and_run":
                    code = data.get("code", "")
                    if code:
                        handler.handle_compile_and_run(code)

                elif msg_type == "stdin":
                    stdin_data = data.get("data", "")
                    handler.handle_stdin(stdin_data)

                elif msg_type == "stop":
                    handler.handle_stop()

                elif msg_type == "ping":
                    try:
                        ws.send(json.dumps({"type": "pong"}))
                    except Exception:
                        pass

        except Exception as e:
            logger.error("ws_error", error=str(e), type=type(e).__name__)
        finally:
            logger.info("ws_disconnected", path="/ws/run")
