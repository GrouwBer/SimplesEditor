"""
PtyExecutionStrategy — Execucao interativa via PTY no sandbox Docker.

Fornece uma interface de terminal (pseudo-terminal) para execucao de
binarios dentro do container sandbox, permitindo:
  - I/O interativo (leia/escreva do SIMPLES)
  - Streaming em tempo real de stdout/stderr
  - Envio de stdin
  - Controle de timeout
  - Sinal de stop (SIGTERM → SIGKILL)
"""

import os
import select
import socket
import threading
import time
from typing import Callable

from logging_config import get_logger
from sandbox_config import APP_CONFIG, get_sandbox_run_kwargs
from app import ACTIVE_CONTAINERS

# Logger do modulo
logger = get_logger(__name__)


# Tempo entre ciclos de leitura do socket (segundos)
_POLL_INTERVAL = 0.05
# Tamanho maximo do buffer de leitura
_BUF_SIZE = 4096


class PtyExecutionError(Exception):
    """Erro durante execucao PTY."""

    pass


class PtyExecutionStrategy:
    """
    Estrategia de execucao usando PTY (pseudo-terminal) no Docker.

    Cria um container com TTY alocado e stdin aberto, permitindo
    comunicacao bidirecional em tempo real via socket Docker attach.

    Uso:
        strategy = PtyExecutionStrategy()
        strategy.start("/sandbox/prog")

        # Em threads separadas:
        strategy.on_stdout(lambda data: ws.send(data))
        strategy.read_loop()

        # Para enviar stdin:
        strategy.write_stdin("entrada do usuario\\n")

        # Para parar:
        strategy.stop()
    """

    def __init__(self, timeout: int | None = None):
        self.timeout = timeout or APP_CONFIG["timeout"]
        self._container = None
        self._sock: socket.socket | None = None
        self._running = False
        self._timed_out = False
        self._exit_code: int | None = None
        self._lock = threading.Lock()
        self._stdout_callback: Callable[[str], None] | None = None
        self._stderr_callback: Callable[[str], None] | None = None
        self._exit_callback: Callable[[int | None, bool], None] | None = None

    # ---------------------------------------------------------------
    # Propriedades
    # ---------------------------------------------------------------

    @property
    def timed_out(self) -> bool:
        return self._timed_out

    @property
    def exit_code(self) -> int | None:
        return self._exit_code

    # ---------------------------------------------------------------
    # Callbacks
    # ---------------------------------------------------------------

    def on_stdout(self, callback: Callable[[str], None]):
        """Registra callback para dados de stdout."""
        self._stdout_callback = callback

    def on_stderr(self, callback: Callable[[str], None]):
        """Registra callback para dados de stderr."""
        self._stderr_callback = callback

    def on_exit(self, callback: Callable[[int | None, bool], None]):
        """
        Registra callback para saida da execucao.

        Args:
            callback: Recebe (exit_code, timed_out)
        """
        self._exit_callback = callback

    # ---------------------------------------------------------------
    # API publica
    # ---------------------------------------------------------------

    def start(self, binary_path: str) -> None:
        """
        Inicia o container com PTY.

        Cria um container Docker com tty=True e stdin_open=True,
        depois anexa um socket para comunicacao bidirecional.

        Args:
            binary_path: Caminho do binario dentro do container.

        Raises:
            PtyExecutionError: Se falhar ao criar/anexar ao container.
        """
        import docker
        from docker.errors import DockerException

        try:
            client = docker.from_env()

            run_kwargs = get_sandbox_run_kwargs()

            # Bind mount do diretorio do binario
            binary_dir = os.path.dirname(binary_path)
            binary_name = os.path.basename(binary_path)
            host_binary_dir = os.path.normpath(binary_dir)

            run_kwargs["volumes"] = {
                host_binary_dir: {
                    "bind": "/sandbox",
                    "mode": "ro",
                }
            }

            # Configuracoes PTY
            run_kwargs["tty"] = True
            run_kwargs["stdin_open"] = True
            run_kwargs["detach"] = True

            self._container = client.containers.run(
                image=APP_CONFIG["sandbox_image"],
                command=["/sandbox/" + binary_name],
                **run_kwargs,
            )

            ACTIVE_CONTAINERS.inc()
            logger.info(
                "pty_container_started",
                container_id=self._container.id[:12],
                binary=binary_name,
            )

            # Anexa socket para I/O
            self._sock = self._container.attach_socket(
                params={"stdin": 1, "stdout": 1, "stderr": 1}
            )

            # O socket do docker-py retorna um socket duplo (stdin/stdout)
            # Precisamos do socket bruto para leitura/escrita
            if hasattr(self._sock, "_sock"):
                self._sock = self._sock._sock

            self._running = True

        except DockerException as e:
            ACTIVE_CONTAINERS.dec()
            logger.error("pty_docker_error", error=str(e))
            raise PtyExecutionError(f"Erro Docker ao iniciar PTY: {e}")

    def write_stdin(self, data: str) -> None:
        """
        Escreve dados no stdin do container (PTY).

        Args:
            data: Dados a enviar (string).
        """
        if not self._sock or not self._running:
            return
        try:
            self._sock.sendall(data.encode("utf-8"))
        except Exception as e:
            logger.error("pty_stdin_error", error=str(e))

    def read_loop(self) -> None:
        """
        Loop de leitura do PTY.

        Chama os callbacks registrados para stdout/stderr
        e monitora timeout. Bloqueia ate a execucao terminar.

        Deve ser executado em uma thread separada.
        """
        start_time = time.monotonic()
        deadline = start_time + self.timeout

        try:
            while self._running and time.monotonic() < deadline:
                if not self._sock:
                    break

                # Verifica se o socket tem dados para ler
                ready, _, _ = select.select([self._sock], [], [], _POLL_INTERVAL)

                if ready:
                    try:
                        data = self._sock.recv(_BUF_SIZE)
                        if not data:
                            # Socket fechou
                            break

                        # Processa dados (formato multiplexado do Docker)
                        self._process_docker_data(data)

                    except (socket.timeout, BlockingIOError):
                        continue
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        break

                # Verifica se o container ja terminou
                try:
                    self._container.reload()
                    if self._container.status == "exited":
                        self._exit_code = self._container.attrs["State"]["ExitCode"]
                        break
                except Exception:
                    break

            # Verifica timeout
            if time.monotonic() >= deadline and self._running:
                self._timed_out = True
                logger.warning("pty_timeout", timeout=self.timeout)
                self._stop_container()

        except Exception as e:
            logger.error("pty_read_loop_error", error=str(e))
        finally:
            self._running = False
            self._cleanup()

            # Notifica saida
            if self._exit_callback:
                self._exit_callback(self._exit_code, self._timed_out)

    def stop(self) -> None:
        """
        Para a execucao: SIGTERM → SIGKILL.

        Envia SIGTERM, aguarda 1s, depois SIGKILL se ainda ativo.
        """
        logger.info("pty_stop_requested")

        if not self._container:
            self._running = False
            return

        try:
            # SIGTERM
            self._container.exec_run(
                "kill -TERM 1 2>/dev/null; exit 0",
                user="root",
            )
            time.sleep(1)

            # Verifica se ainda esta rodando
            self._container.reload()
            if self._container.status == "exited":
                return

            # SIGKILL
            self._container.kill()

        except Exception as e:
            logger.error("pty_stop_error", error=str(e))

    # ---------------------------------------------------------------
    # Metodos internos
    # ---------------------------------------------------------------

    def _process_docker_data(self, data: bytes) -> None:
        """
        Processa dados no formato multiplexado do Docker.

        O Docker attach usa um header de 8 bytes:
          [byte 0: stream type (1=stdin, 2=stdout, 3=stderr)]
          [bytes 1-3: padding]
          [bytes 4-7: payload size (big-endian uint32)]
          [payload]

        Se nao for multiplexado (tty=True), os dados sao raw.
        """
        if not data:
            return

        if self._is_multiplexed(data):
            self._process_multiplexed(data)
        else:
            # Modo TTY: dados raw
            text = data.decode("utf-8", errors="replace")
            if self._stdout_callback:
                self._stdout_callback(text)

    @staticmethod
    def _is_multiplexed(data: bytes) -> bool:
        """
        Verifica se os dados estao no formato multiplexado do Docker.

        No modo TTY, o Docker NAO multiplexa, entao verificamos
        se o primeiro byte parece um header valido.
        """
        if len(data) < 9:
            return False
        # Header multiplexado: byte 0 = 1, 2 ou 3
        return data[0] in (1, 2, 3)

    def _process_multiplexed(self, data: bytes) -> None:
        """Processa dados multiplexados do Docker (modo nao-TTY)."""
        offset = 0
        while offset + 8 <= len(data):
            stream_type = data[offset]  # 1=stdin, 2=stdout, 3=stderr
            payload_size = int.from_bytes(data[offset + 4:offset + 8], "big")
            offset += 8

            if payload_size == 0:
                continue

            payload = data[offset:offset + payload_size]
            offset += payload_size

            text = payload.decode("utf-8", errors="replace")

            if stream_type == 2 and self._stdout_callback:
                self._stdout_callback(text)
            elif stream_type == 3 and self._stderr_callback:
                self._stderr_callback(text)
            elif stream_type == 1:
                # Echo do stdin (ignorar)
                pass

    def _stop_container(self) -> None:
        """Para e remove o container."""
        if not self._container:
            return
        try:
            self._container.stop(timeout=10)
        except Exception:
            try:
                self._container.kill()
            except Exception:
                pass

    def _cleanup(self) -> None:
        """Remove o container e fecha recursos."""
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        if self._container:
            try:
                self._container.remove(force=True)
            except Exception:
                pass
            self._container = None

        ACTIVE_CONTAINERS.dec()
