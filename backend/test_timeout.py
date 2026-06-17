"""
Testes do enforcement de timeout para compilacao e execucao.
"""

import subprocess
import sys
import time

import pytest
from sandbox_config import APP_CONFIG


# ============================================================
# Testes: get_compile_timeout
# ============================================================

class TestCompileTimeoutConfig:

    def test_compile_timeout_default_is_15(self):
        """Timeout de compilacao padrao deve ser 15s (RF15)."""
        from timeout_enforcer import get_compile_timeout
        assert get_compile_timeout() == 15

    def test_exec_timeout_default_is_10(self):
        """Timeout de execucao padrao deve ser 10s (RF14)."""
        from timeout_enforcer import get_exec_timeout
        assert get_exec_timeout() == 10

    def test_compile_timeout_from_config(self):
        """compile_timeout deve vir do APP_CONFIG."""
        assert APP_CONFIG["compile_timeout"] == 15

    def test_exec_timeout_from_config(self):
        """timeout (execucao) deve vir do APP_CONFIG."""
        assert APP_CONFIG["timeout"] == 10


# ============================================================
# Testes: run_with_timeout
# ============================================================

class TestRunWithTimeout:

    def test_quick_command_succeeds(self):
        """Comando rapido deve retornar normalmente."""
        from timeout_enforcer import run_with_timeout

        result = run_with_timeout(
            [sys.executable, "-c", "print('ok')"],
            timeout=5,
        )

        assert result.returncode == 0
        assert b"ok" in result.stdout

    def test_timeout_expired_raises_error(self):
        """Comando que excede o timeout deve lancar TimeoutError."""
        from timeout_enforcer import run_with_timeout, TimeoutError

        with pytest.raises(TimeoutError) as excinfo:
            run_with_timeout(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                timeout=1,  # timeout de 1s
            )

        assert excinfo.value.timeout_s == 1
        assert "excedeu o timeout" in excinfo.value.output

    def test_default_timeout_from_config(self, monkeypatch):
        """Timeout padrao deve vir do APP_CONFIG quando nao especificado."""
        from timeout_enforcer import run_with_timeout, TimeoutError

        # Comando rapido com timeout=None deve usar o compile_timeout (15s)
        # mas como 15s e muito para teste, verificamos que timeout=None
        # nao causa erro para comando rapido
        result = run_with_timeout(
            [sys.executable, "-c", "print('ok')"],
            timeout=None,  # usa padrao compile_timeout
        )

        assert result.returncode == 0

    def test_stdin_is_passed_to_process(self):
        """Stdin deve ser passado para o processo."""
        from timeout_enforcer import run_with_timeout

        result = run_with_timeout(
            [sys.executable, "-c", "import sys; print(sys.stdin.read())"],
            stdin="hello stdin",
            timeout=5,
        )

        assert b"hello stdin" in result.stdout


# ============================================================
# Testes: format_timeout_error
# ============================================================

class TestFormatTimeoutError:

    def test_format_default_message(self):
        """Mensagem padrao de timeout."""
        from timeout_enforcer import format_timeout_error

        msg = format_timeout_error(15)
        assert "15s" in msg
        assert "compilacao" in msg or "Compilacao" in msg

    def test_format_with_custom_phase(self):
        """Mensagem com fase personalizada."""
        from timeout_enforcer import format_timeout_error

        msg = format_timeout_error(10, phase="execucao")
        assert "10s" in msg
        assert "Execucao" in msg or "execucao" in msg

    def test_format_with_loop_infinite_hint(self):
        """Mensagem deve mencionar loop infinito."""
        from timeout_enforcer import format_timeout_error

        msg = format_timeout_error(11)
        assert "loop" in msg.lower()


# ============================================================
# Testes: TimeoutError
# ============================================================

class TestTimeoutError:

    def test_is_subprocess_timeout_expired(self):
        """TimeoutError deve herdar de subprocess.TimeoutExpired."""
        from timeout_enforcer import TimeoutError

        assert issubclass(TimeoutError, subprocess.TimeoutExpired)

    def test_stores_cmd_and_timeout(self):
        """TimeoutError deve armazenar cmd e timeout."""
        from timeout_enforcer import TimeoutError

        err = TimeoutError(
            cmd=["simplesc", "test.simples"],
            timeout=15,
            output="timeout",
        )

        assert err.timeout_s == 15
        assert "simplesc" in err.cmd_str

    def test_can_be_caught_as_timeout_expired(self):
        """TimeoutError deve ser capturavel como subprocess.TimeoutExpired."""
        from timeout_enforcer import TimeoutError

        try:
            raise TimeoutError(cmd=["test"], timeout=15, output="")
        except subprocess.TimeoutExpired:
            pass  # OK
        except Exception:
            pytest.fail("TimeoutError nao foi capturado como TimeoutExpired")


# ============================================================
# Testes: RF14 e RF15 - criterios de aceite
# ============================================================

class TestAcceptanceCriteria:

    def test_rf15_compile_timeout_15s(self):
        """RF15 - Compilacao interrompida apos 15s.

        O timeout de compilacao e de 15s. Um loop de compilacao
        infinito deve ser interrompido.
        """
        from timeout_enforcer import get_compile_timeout
        assert get_compile_timeout() == 15

    def test_rf14_exec_timeout_10s(self):
        """RF14 - Execucao interrompida apos 10s wall-clock.

        Um loop infinito no codigo do aluno deve ser interrompido
        em ~11s (10s timeout + 1s margem).
        """
        from timeout_enforcer import get_exec_timeout
        assert get_exec_timeout() == 10

    def test_infinite_loop_interrupted_under_11s_tolerance(self):
        """Loop infinito interrompido em ~11s (10s + margem).

        Simula um loop infinito com timeout de 1s (em vez de 10s
        para velocidade do teste) e verifica que e interrompido.
        """
        from timeout_enforcer import run_with_timeout, TimeoutError

        start = time.monotonic()
        try:
            run_with_timeout(
                [sys.executable, "-c", "while True: pass"],
                timeout=1,
            )
            pytest.fail("Deveria ter lancado TimeoutError")
        except TimeoutError:
            elapsed = time.monotonic() - start
            # Deve ter sido interrompido em ate 3s (1s timeout + margem)
            assert elapsed < 3.0, (
                f"Loop infinito levou {elapsed:.2f}s para ser interrompido"
            )
