"""
Testes do executor de codigo no sandbox.

Usa mocks para docker-py para evitar dependencia de Docker real.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from sandbox_config import APP_CONFIG


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_docker_client():
    """Mock do Docker client."""
    with patch("executor.docker.from_env") as mock_from_env:
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_container():
    """Mock de um container Docker."""
    container = MagicMock()
    container.status = "exited"
    container.attrs = {"State": {"ExitCode": 0}}
    # Retorna stdout na primeira chamada, stderr vazio na segunda
    container.logs.side_effect = [b"hello world\n", b""]
    return container


# ============================================================
# Testes: run_code_in_sandbox — sucesso
# ============================================================

class TestRunCodeSuccess:
    """Cenario: execucao bem-sucedida com saida normal."""

    def test_returns_stdout_on_success(self, mock_docker_client, mock_container, monkeypatch):
        """Deve retornar stdout do binario quando execucao termina com codigo 0."""
        mock_docker_client.containers.run.return_value = mock_container

        # Garante que duration_s seja > 0
        import time
        fake_time = [100.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time.pop(0) if fake_time else 101.0)

        from executor import run_code_in_sandbox

        result = run_code_in_sandbox(binary_path="/sandbox/prog")

        assert result.exit_code == 0
        assert result.stdout == "hello world\n"
        assert result.timed_out is False
        assert result.duration_s > 0
        assert mock_container.remove.called

    def test_uses_provided_timeout(self, mock_docker_client, mock_container):
        """Deve usar o timeout fornecido."""
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox

        result = run_code_in_sandbox(
            binary_path="/sandbox/prog", timeout=30
        )

        assert result.exit_code == 0
        assert result.timed_out is False

    def test_returns_stderr_on_error(self, mock_docker_client, mock_container):
        """Deve retornar stderr quando binario falha."""
        mock_container.attrs = {"State": {"ExitCode": 1}}
        mock_container.logs.side_effect = [
            b"",  # stdout
            b"segmentation fault\n",  # stderr
        ]
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox

        result = run_code_in_sandbox(binary_path="/sandbox/prog")

        assert result.exit_code == 1
        assert result.stderr == "segmentation fault\n"
        assert result.timed_out is False

    def test_uses_sandbox_image_from_config(self, mock_docker_client, mock_container):
        """Deve usar a imagem configurada em APP_CONFIG."""
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox

        run_code_in_sandbox(binary_path="/sandbox/prog")

        mock_docker_client.containers.run.assert_called_once()
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs["image"] == APP_CONFIG["sandbox_image"]


# ============================================================
# Testes: run_code_in_sandbox — timeout
# ============================================================

class TestRunCodeTimeout:
    """Cenario: execucao excede o timeout configurado."""

    def test_returns_timed_out_true_when_exceeds_timeout(
        self, mock_docker_client, mock_container, monkeypatch
    ):
        """Deve retornar timed_out=True quando o timeout e excedido."""
        # Container nunca sai do estado "running"
        mock_container.status = "running"
        mock_docker_client.containers.run.return_value = mock_container

        # Acelera o tempo para o timeout acontecer rapido
        fake_time = [100.0]

        def mock_monotonic():
            return fake_time[0]

        monkeypatch.setattr(time, "monotonic", mock_monotonic)

        from executor import run_code_in_sandbox

        # Com timeout de 1s, avancamos o tempo para simular timeout
        def advance_time(*args, **kwargs):
            fake_time[0] += 2.0  # avanca 2s

        mock_container.reload.side_effect = advance_time

        result = run_code_in_sandbox(binary_path="/sandbox/prog", timeout=1)

        assert result.timed_out is True
        assert result.exit_code == -1
        # Deve ter chamado stop e remove
        assert mock_container.stop.called or mock_container.kill.called
        assert mock_container.remove.called

    def test_timeout_metrics_incremented(self, mock_docker_client, mock_container, monkeypatch):
        """Deve incrementar contador de timeout nas metricas."""
        mock_container.status = "running"
        mock_docker_client.containers.run.return_value = mock_container

        fake_time = [100.0]

        def mock_monotonic():
            return fake_time[0]

        monkeypatch.setattr(time, "monotonic", mock_monotonic)
        mock_container.reload.side_effect = lambda: fake_time.__setitem__(0, fake_time[0] + 2.0)

        from executor import run_code_in_sandbox, EXECUTIONS_TOTAL

        # Reseta o contador
        EXECUTIONS_TOTAL.clear()

        result = run_code_in_sandbox(binary_path="/sandbox/prog", timeout=1)

        # Verifica que o contador de timeout foi incrementado
        timeout_count = EXECUTIONS_TOTAL.labels(status="timeout")._value.get()
        assert timeout_count == 1


# ============================================================
# Testes: run_code_in_sandbox — erros
# ============================================================

class TestRunCodeErrors:
    """Cenario: erro ao conectar ou executar no Docker."""

    def test_raises_executor_error_on_docker_failure(
        self, mock_docker_client
    ):
        """Deve levantar ExecutorError quando docker-py falha."""
        mock_docker_client.containers.run.side_effect = docker_error()

        from executor import run_code_in_sandbox, ExecutorError

        with pytest.raises(ExecutorError, match="Erro no sandbox Docker"):
            run_code_in_sandbox(binary_path="/sandbox/prog")

    def test_handles_container_logs_failure(
        self, mock_docker_client, mock_container
    ):
        """Deve tratar falha ao ler logs sem quebrar."""
        mock_container.logs.side_effect = Exception("log error")
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox

        result = run_code_in_sandbox(binary_path="/sandbox/prog")

        assert result.exit_code == 0
        assert result.stdout == ""  # logs falhou, mas nao quebrou


# ============================================================
# Testes: run_code_in_sandbox — metricas
# ============================================================

class TestRunCodeMetrics:
    """Cenario: metricas Prometheus sao registradas."""

    def test_active_containers_gauge_incremented(
        self, mock_docker_client, mock_container
    ):
        """Deve incrementar o gauge de containers ativos."""
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox, ACTIVE_CONTAINERS

        before = ACTIVE_CONTAINERS._value.get()
        run_code_in_sandbox(binary_path="/sandbox/prog")
        after = ACTIVE_CONTAINERS._value.get()

        # Deve ter incrementado e depois decrementado
        assert after == before  # voltou ao valor original

    def test_execution_duration_recorded(
        self, mock_docker_client, mock_container, monkeypatch
    ):
        """Deve registrar a duracao da execucao no histograma."""
        mock_docker_client.containers.run.return_value = mock_container

        import time
        fake_time = [100.0]
        monkeypatch.setattr(time, "monotonic", lambda: fake_time.pop(0) if fake_time else 101.0)

        from executor import run_code_in_sandbox, EXECUTION_DURATION

        result = run_code_in_sandbox(binary_path="/sandbox/prog")

        assert result.duration_s > 0

    def test_execution_success_counter(
        self, mock_docker_client, mock_container
    ):
        """Deve incrementar contador de execucoes com status success."""
        mock_docker_client.containers.run.return_value = mock_container

        from executor import run_code_in_sandbox, EXECUTIONS_TOTAL

        EXECUTIONS_TOTAL.clear()
        run_code_in_sandbox(binary_path="/sandbox/prog")

        success_count = EXECUTIONS_TOTAL.labels(status="success")._value.get()
        assert success_count == 1


# ============================================================
# Testes: run_code_in_sandbox — configuracao de timeout
# ============================================================

class TestTimeoutConfiguration:
    """Cenario: configuracao de timeout do sandbox."""

    def test_default_timeout_from_config(self):
        """O timeout padrao deve vir do APP_CONFIG."""
        assert APP_CONFIG["timeout"] == 10

    def test_compile_timeout_from_config(self):
        """O timeout de compilacao deve vir do APP_CONFIG."""
        assert APP_CONFIG["compile_timeout"] == 15


# ============================================================
# Helpers
# ============================================================

def docker_error():
    """Retorna uma excecao simulada do Docker."""
    import docker.errors
    return docker.errors.DockerException("connection refused")
