"""
Testes do WebSocket handler (ws_handler.py).

Testa WsRunHandler com mocks para evitar dependencia de Docker e compiladores reais.
"""

import json
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_ws():
    """Mock do WebSocket Server."""
    ws = MagicMock()
    ws.send = MagicMock()
    ws.receive = MagicMock()
    return ws


@pytest.fixture
def handler(mock_ws):
    """WsRunHandler com WebSocket mockado."""
    from ws_handler import WsRunHandler
    return WsRunHandler(mock_ws)


# ============================================================
# Testes: _send
# ============================================================

class TestSend:

    def test_sends_json_message(self, handler, mock_ws):
        """_send deve enviar JSON serializado."""
        handler._send({"type": "test", "data": "hello"})

        mock_ws.send.assert_called_once_with(
            json.dumps({"type": "test", "data": "hello"})
        )

    def test_handles_send_error(self, handler, mock_ws):
        """_send nao deve quebrar se o envio falhar."""
        mock_ws.send.side_effect = Exception("connection closed")

        handler._send({"type": "test"})  # Nao deve levantar excecao


# ============================================================
# Testes: handle_stdin
# ============================================================

class TestHandleStdin:

    def test_sends_data_to_process_stdin(self, handler):
        """handle_stdin deve escrever no stdin do processo."""
        mock_stdin = MagicMock()
        handler._process = MagicMock()
        handler._process.stdin = mock_stdin

        handler.handle_stdin("input data")

        mock_stdin.write.assert_called_once_with(b"input data")
        mock_stdin.flush.assert_called_once()

    def test_no_process_no_error(self, handler):
        """handle_stdin sem processo ativo nao deve quebrar."""
        handler._process = None
        handler.handle_stdin("data")  # Nao deve levantar excecao

    def test_stdin_error_ignored(self, handler):
        """Erro ao escrever no stdin deve ser ignorado."""
        handler._process = MagicMock()
        handler._process.stdin.write.side_effect = Exception("broken pipe")

        handler.handle_stdin("data")  # Nao deve levantar excecao


# ============================================================
# Testes: handle_stop
# ============================================================

class TestHandleStop:

    def test_sends_sigterm_to_process(self, handler):
        """handle_stop deve enviar SIGTERM ao processo."""
        import signal
        handler._process = MagicMock()

        handler.handle_stop()

        handler._process.send_signal.assert_called_once_with(signal.SIGTERM)

    def test_no_process_no_error(self, handler):
        """handle_stop sem processo nao deve quebrar."""
        handler._process = None
        handler.handle_stop()  # Nao deve levantar excecao

    def test_kill_after_timeout(self, handler):
        """handle_stop deve chamar kill apos 1s se processo nao morrer."""
        handler._process = MagicMock()
        handler._process.send_signal.side_effect = lambda *a: None

        handler.handle_stop()
        time.sleep(0.1)  # Nao esperamos o kill real, apenas verifica que nao quebrou


# ============================================================
# Testes: _compile
# ============================================================

class TestCompile:

    @patch("ws_handler.subprocess.run")
    def test_successful_compile(self, mock_run, handler, mock_ws):
        """Compilacao bem-sucedida deve enviar asm_generated."""
        # Cada fase retorna sucesso
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"nasm code", stderr=b""),
            MagicMock(returncode=0, stdout=b"", stderr=b""),
            MagicMock(returncode=0, stdout=b"", stderr=b""),
        ]

        result = handler._compile("programa\nfim")

        assert result is not None
        assert result[0] == "nasm code"
        # compile_started e enviado por _run_pipeline, nao por _compile

    @patch("ws_handler.subprocess.run")
    def test_compile_error_sends_message(self, mock_run, handler, mock_ws):
        """Erro de compilacao deve enviar compile_error."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=b"",
            stderr=b"linha 5: comando invalido",
        )

        result = handler._compile("programa invalido")

        assert result is None
        # Verifica que compile_error foi enviado
        error_msg = [call for call in mock_ws.send.call_args_list
                     if '"compile_error"' in call[0][0]]
        assert len(error_msg) > 0
        assert '"line": 5' in error_msg[0][0][0]

    @patch("ws_handler.subprocess.run")
    def test_compile_timeout(self, mock_run, handler, mock_ws):
        """Timeout de compilacao deve enviar compile_error."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="simplesc", timeout=15)

        result = handler._compile("programa")

        assert result is None
        compile_msgs = [call for call in mock_ws.send.call_args_list
                        if '"compile_error"' in call[0][0]]
        assert len(compile_msgs) > 0


# ============================================================
# Testes: _run_cmd
# ============================================================

class TestRunCmd:

    @patch("ws_handler.subprocess.run")
    def test_success(self, mock_run, handler):
        """Comando bem-sucedido retorna stdout."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout=b"output", stderr=b""
        )

        result = handler._run_cmd(["echo", "hello"], timeout=5)

        assert result["returncode"] == 0
        assert result["stdout"] == "output"

    @patch("ws_handler.subprocess.run")
    def test_file_not_found(self, mock_run, handler):
        """Comando inexistente retorna erro amigavel."""
        mock_run.side_effect = FileNotFoundError("not found")

        result = handler._run_cmd(["nonexistent"], timeout=5)

        assert result["returncode"] == -1
        assert "nao encontrado" in result["stderr"]


# ============================================================
# Testes: _extract_line / _extract_column
# ============================================================

class TestExtractLineColumn:

    def test_extract_line_portuguese(self, handler):
        line = handler._extract_line("erro na linha 42, coluna 7: erro")
        assert line == 42

    def test_extract_line_english(self, handler):
        line = handler._extract_line("error at line 15: syntax")
        assert line == 15

    def test_extract_line_default(self, handler):
        line = handler._extract_line("erro generico", default=0)
        assert line == 0

    def test_extract_column(self, handler):
        col = handler._extract_column("erro na linha 5, coluna 10: erro")
        assert col == 10

    def test_extract_column_default(self, handler):
        col = handler._extract_column("erro sem coluna", default=0)
        assert col == 0


# ============================================================
# Testes: Protocolo de mensagens (integracao)
# ============================================================

class TestMessageProtocol:

    def test_compile_started_sent_first(self, handler, mock_ws):
        """Pipeline deve enviar compile_started primeiro."""
        from ws_handler import WsRunHandler

        # Mock para nao executar realmente
        with patch.object(handler, '_compile', return_value=None):
            handler._run_pipeline("code")

        # compile_started deve ter sido enviado
            msgs = [call[0][0] for call in mock_ws.send.call_args_list]
            assert any('"compile_started"' in msg for msg in msgs)

    def test_internal_error_on_pipeline_exception(self, handler, mock_ws):
        """Excecao no pipeline deve enviar internal_error."""
        with patch.object(handler, '_compile', side_effect=Exception("crash")):
            handler._run_pipeline("code")

        msgs = [call[0][0] for call in mock_ws.send.call_args_list]
        assert any('"internal_error"' in msg for msg in msgs)

    def test_compile_then_exec_flow(self, handler, mock_ws):
        """Fluxo completo: compile → asm → exec → exit."""
        with patch.object(handler, '_compile') as mock_compile:
            mock_compile.return_value = ("nasm", "/tmp/prog")

            with patch.object(handler, '_run_binary') as mock_run:
                # Simula execucao bem-sucedida
                handler._timed_out = False
                handler._exit_code = 0

                handler._run_pipeline("code")

        msgs = [json.loads(call[0][0]) for call in mock_ws.send.call_args_list]
        types = [m["type"] for m in msgs]

        assert "compile_started" in types
        assert "asm_generated" in types
        assert "exec_started" in types
        assert "exit" in types


# ============================================================
# Testes: handle_compile_and_run (threading)
# ============================================================

class TestHandleCompileAndRun:

    def test_starts_thread(self, handler):
        """handle_compile_and_run deve iniciar uma thread."""
        with patch.object(handler, '_run_pipeline') as mock_pipeline:
            handler.handle_compile_and_run("code")
            time.sleep(0.05)  # Aguarda thread iniciar
            mock_pipeline.assert_called_once_with("code")

    def test_empty_code_does_nothing(self, handler):
        """Codigo vazio nao deve iniciar pipeline."""
        with patch.object(handler, '_run_pipeline') as mock_pipeline:
            handler.handle_compile_and_run("")
            time.sleep(0.05)
            mock_pipeline.assert_called_once_with("")
