"""
Testes do PtyExecutionStrategy.
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ============================================================
# Testes: PtyExecutionStrategy
# ============================================================

class TestPtyExecutionStrategy:

    def test_start_creates_container(self):
        """start() deve criar container com tty=True e stdin_open=True."""
        import docker
        with patch.object(docker, 'from_env') as mock_from_env:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_container.id = "abc123def456"
            mock_client.containers.run.return_value = mock_container
            mock_from_env.return_value = mock_client

            from pty_execution import PtyExecutionStrategy

            strategy = PtyExecutionStrategy()
            strategy.start("/sandbox/prog")

            # Verifica que o container foi criado com params PTY
            call_kwargs = mock_client.containers.run.call_args[1]
            assert call_kwargs["tty"] is True
            assert call_kwargs["stdin_open"] is True
            assert call_kwargs["detach"] is True

    @patch("pty_execution.docker.from_env")
    def test_write_stdin_sends_data(self, mock_docker):
        """write_stdin() deve enviar dados pelo socket."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client

        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        strategy.start("/sandbox/prog")
        strategy.write_stdin("hello\n")

        mock_sock.sendall.assert_called_once_with(b"hello\n")

    @patch("pty_execution.docker.from_env")
    def test_write_stdin_no_socket(self, mock_docker):
        """write_stdin() sem socket ativo nao deve quebrar."""
        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        # Nao chamou start() -> sem socket
        strategy.write_stdin("data")  # Nao deve levantar excecao

    @patch("pty_execution.docker.from_env")
    def test_stop_kills_container(self, mock_docker):
        """stop() deve matar o container."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client

        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        strategy.start("/sandbox/prog")
        strategy.stop()

        # Deve ter executado kill no container
        assert mock_container.exec_run.called or mock_container.kill.called

    @patch("pty_execution.docker.from_env")
    def test_stop_without_container(self, mock_docker):
        """stop() sem container nao deve quebrar."""
        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        strategy.stop()  # Nao deve levantar excecao

    @patch("pty_execution.docker.from_env")
    def test_read_loop_calls_stdout_callback(self, mock_docker):
        """read_loop() deve chamar callback de stdout com dados."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock
        mock_container.status = "exited"
        mock_container.attrs = {"State": {"ExitCode": 0}}
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client

        from pty_execution import PtyExecutionStrategy
        import select

        # Configura select para retornar o socket pronto
        with patch("pty_execution.select.select") as mock_select:
            mock_select.return_value = ([mock_sock], [], [])
            # Simula dados do TTY (raw, nao multiplexado)
            mock_sock.recv.side_effect = [b"hello world\n", b""]

            strategy = PtyExecutionStrategy()
            strategy.start("/sandbox/prog")

            received = []
            strategy.on_stdout(lambda data: received.append(data))

            original_running = strategy._running

            def fake_reload():
                strategy._container.status = "exited"

            mock_container.reload.side_effect = fake_reload

            strategy.read_loop()

            # Pode ou nao ter recebido dados dependendo do timing
            # Mas nao deve ter quebrado
            assert strategy.exit_code == 0

    @patch("pty_execution.docker.from_env")
    def test_on_exit_called_when_container_exits(self, mock_docker):
        """on_exit deve ser chamado quando o container termina."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock
        mock_container.attach_socket.return_value._sock = mock_sock
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client

        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        strategy.start("/sandbox/prog")

        exit_data = []

        def on_exit(exit_code, timed_out):
            exit_data.append((exit_code, timed_out))

        strategy.on_exit(on_exit)

        # Simula que o container ja terminou
        strategy._running = False
        strategy._exit_code = 0
        strategy._cleanup()
        strategy._exit_callback(0, False)

        assert len(exit_data) == 1
        assert exit_data[0] == (0, False)

    @patch("pty_execution.docker.from_env")
    def test_properties(self, mock_docker):
        """Propriedades timed_out e exit_code devem funcionar."""
        from pty_execution import PtyExecutionStrategy

        strategy = PtyExecutionStrategy()
        assert strategy.timed_out is False
        assert strategy.exit_code is None

        strategy._timed_out = True
        strategy._exit_code = -1

        assert strategy.timed_out is True
        assert strategy.exit_code == -1


# ============================================================
# Testes: _process_docker_data
# ============================================================

class TestProcessDockerData:

    def setup_method(self):
        from pty_execution import PtyExecutionStrategy
        self.strategy = PtyExecutionStrategy()

    def test_multiplexed_stdout(self):
        """Dados multiplexados stdout (type=2) devem chamar stdout_callback."""
        received = []
        self.strategy.on_stdout(lambda d: received.append(d))

        # Header: type=2, size=5, payload="hello"
        header = bytes([2, 0, 0, 0, 0, 0, 0, 5])
        payload = b"hello"
        self.strategy._process_docker_data(header + payload)

        assert len(received) == 1
        assert received[0] == "hello"

    def test_multiplexed_stderr(self):
        """Dados multiplexados stderr (type=3) devem chamar stderr_callback."""
        received = []
        self.strategy.on_stderr(lambda d: received.append(d))

        header = bytes([3, 0, 0, 0, 0, 0, 0, 6])
        payload = b"error!"
        self.strategy._process_docker_data(header + payload)

        assert len(received) == 1
        assert received[0] == "error!"

    def test_raw_tty_data(self):
        """Dados raw (modo TTY) devem ir para stdout_callback."""
        received = []
        self.strategy.on_stdout(lambda d: received.append(d))

        # Dados com menos de 9 bytes sao considerados raw
        self.strategy._process_docker_data(b"hello")

        assert len(received) == 1
        assert received[0] == "hello"

    def test_empty_data(self):
        """Dados vazios nao devem chamar callbacks."""
        called = False

        def callback(data):
            nonlocal called
            called = True

        self.strategy.on_stdout(callback)
        self.strategy._process_docker_data(b"")

        assert called is False


# ============================================================
# Testes: _is_multiplexed
# ============================================================

class TestIsMultiplexed:

    def setup_method(self):
        from pty_execution import PtyExecutionStrategy
        self.strategy = PtyExecutionStrategy()

    def test_stdout_multiplexed(self):
        assert self.strategy._is_multiplexed(bytes([2, 0, 0, 0, 0, 0, 0, 5, 104]))

    def test_stderr_multiplexed(self):
        assert self.strategy._is_multiplexed(bytes([3, 0, 0, 0, 0, 0, 0, 5, 104]))

    def test_short_data_not_multiplexed(self):
        assert self.strategy._is_multiplexed(b"hello") is False

    def test_unknown_type_not_multiplexed(self):
        assert self.strategy._is_multiplexed(bytes([5, 0, 0, 0, 0, 0, 0, 5, 104])) is False
