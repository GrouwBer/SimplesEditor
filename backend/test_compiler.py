"""
Testes do modulo de compilacao (compiler.py) e endpoint /api/compile.

Usa mocking para evitar dependencia de ferramentas externas
(simplesc, nasm, ld).
"""

import json
import os
from unittest.mock import patch, MagicMock, call

import pytest
from app import app
from sandbox_config import APP_CONFIG


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================================
# Testes: compile_source — pipeline completo
# ============================================================

class TestCompileSource:
    """Testa compile_source com subprocess mockado."""

    @patch("compiler.subprocess.run")
    def test_successful_compilation(self, mock_run):
        """Pipeline completo: simplesc → nasm → ld com sucesso."""
        # Configura mocks para cada fase
        mock_run.side_effect = [
            MagicMock(  # simplesc
                returncode=0,
                stdout=b"section .text\n  mov eax, 1\n",
                stderr=b"",
            ),
            MagicMock(  # nasm
                returncode=0,
                stdout=b"",
                stderr=b"",
            ),
            MagicMock(  # ld
                returncode=0,
                stdout=b"",
                stderr=b"",
            ),
        ]

        from compiler import compile_source

        result = compile_source("programa\n  escreva 42\nfim")

        assert result.success is True
        assert result.nasm_output == "section .text\n  mov eax, 1\n"
        assert result.binary_path is not None
        assert result.errors == []
        # Duracao pode ser 0 com mocks (tudo instantaneo)
        assert result.duration_s >= 0
        assert set(result.phases.keys()) == {"simplesc", "nasm", "ld"}
        assert set(result.phases.keys()) == {"simplesc", "nasm", "ld"}

    @patch("compiler.subprocess.run")
    def test_simplesc_failure_returns_errors(self, mock_run):
        """Falha no simplesc deve retornar erros com linha/coluna."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=b"",
            stderr=b"erro na linha 5, coluna 10: comando invalido\n",
        )

        from compiler import compile_source

        result = compile_source("programa invalido")

        assert result.success is False
        assert result.binary_path is None
        assert len(result.errors) > 0
        assert result.errors[0]["line"] == 5
        assert result.errors[0]["column"] == 10
        assert "comando invalido" in result.errors[0]["message"]

    @patch("compiler.subprocess.run")
    def test_nasm_failure(self, mock_run):
        """Falha no nasm deve ser reportada."""
        mock_run.side_effect = [
            MagicMock(  # simplesc OK
                returncode=0,
                stdout=b"section .text\n",
                stderr=b"",
            ),
            MagicMock(  # nasm FAIL
                returncode=1,
                stdout=b"",
                stderr=b"error: parser: instruction expected",
            ),
        ]

        from compiler import compile_source

        result = compile_source("programa")

        assert result.success is False
        assert result.nasm_output == "section .text\n"
        assert len(result.errors) > 0

    @patch("compiler.subprocess.run")
    def test_ld_failure(self, mock_run):
        """Falha no ld deve ser reportada."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"nasm", stderr=b""),
            MagicMock(returncode=0, stdout=b"", stderr=b""),
            MagicMock(returncode=1, stdout=b"", stderr=b"undefined reference"),
        ]

        from compiler import compile_source

        result = compile_source("programa")

        assert result.success is False
        assert result.nasm_output == "nasm"
        assert "undefined reference" in result.errors[0]["message"]

    @patch("compiler.subprocess.run")
    def test_timeout_expired(self, mock_run):
        """Timeout deve ser tratado como erro de compilacao."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="simplesc", timeout=15)

        from compiler import compile_source

        result = compile_source("programa")

        assert result.success is False
        assert "timeout" in result.phases.get("simplesc", MagicMock()).error.lower()

    @patch("compiler.subprocess.run")
    def test_file_not_found(self, mock_run):
        """Executavel ausente deve ser tratado como erro."""
        mock_run.side_effect = FileNotFoundError("simplesc not found")

        from compiler import compile_source

        result = compile_source("programa")

        assert result.success is False
        assert "nao encontrado" in result.phases.get("simplesc", MagicMock()).error

    @patch("compiler.subprocess.run")
    def test_compile_metrics_incremented_on_success(self, mock_run):
        """Compilacao bem-sucedida deve incrementar contador Prometheus."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=b"nasm", stderr=b""),
            MagicMock(returncode=0, stdout=b"", stderr=b""),
            MagicMock(returncode=0, stdout=b"", stderr=b""),
        ]

        from compiler import compile_source, COMPILATIONS_TOTAL

        COMPILATIONS_TOTAL.clear()
        compile_source("programa")

        success_count = COMPILATIONS_TOTAL.labels(status="success")._value.get()
        assert success_count == 1

    @patch("compiler.subprocess.run")
    def test_compile_metrics_incremented_on_error(self, mock_run):
        """Compilacao com erro deve incrementar contador de erros."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout=b"", stderr=b"erro"
        )

        from compiler import compile_source, COMPILATIONS_TOTAL

        COMPILATIONS_TOTAL.clear()
        compile_source("programa invalido")

        error_count = COMPILATIONS_TOTAL.labels(status="error")._value.get()
        assert error_count == 1


# ============================================================
# Testes: _parse_simplesc_errors
# ============================================================

class TestParseSimplescErrors:
    """Testa o parser de erros do simplesc."""

    def test_parse_portuguese_format(self):
        """Erro no formato 'erro na linha X, coluna Y: mensagem'."""
        from compiler import _parse_simplesc_errors

        errors = _parse_simplesc_errors(
            "erro na linha 5, coluna 10: comando invalido\n"
        )

        assert len(errors) == 1
        assert errors[0]["line"] == 5
        assert errors[0]["column"] == 10
        assert errors[0]["message"] == "comando invalido"

    def test_parse_gcc_like_format(self):
        """Erro no formato GCC-like 'arquivo:linha:col: mensagem'."""
        from compiler import _parse_simplesc_errors

        errors = _parse_simplesc_errors(
            "source.simples:12:5: error: expected 'fim'\n"
        )

        assert len(errors) == 1
        assert errors[0]["line"] == 12
        assert errors[0]["column"] == 5

    def test_empty_stderr_returns_no_errors(self):
        """Stderr vazio deve retornar lista vazia."""
        from compiler import _parse_simplesc_errors

        errors = _parse_simplesc_errors("")
        assert errors == []

    def test_multiple_errors_parsed(self):
        """Multiplos erros devem ser extraidos."""
        from compiler import _parse_simplesc_errors

        errors = _parse_simplesc_errors(
            "linha 3: comando nao reconhecido\n"
            "linha 7: esperado 'fim'\n"
        )

        assert len(errors) >= 2


# ============================================================
# Testes: /api/compile endpoint
# ============================================================

class TestCompileEndpoint:
    """Testa o endpoint HTTP /api/compile."""

    @patch("compiler.compile_source")
    def test_post_valid_code(self, mock_compile, client):
        """POST com codigo valido deve retornar 200 com NASM."""
        from compiler import CompileResult

        mock_compile.return_value = CompileResult(
            success=True,
            nasm_output="section .text\n  mov eax, 1\n",
            binary_path="/tmp/prog",
            errors=[],
            duration_s=0.5,
            phases={},
        )

        response = client.post(
            "/api/compile",
            data=json.dumps({"code": "programa\n  escreva 42\nfim"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["nasm"] == "section .text\n  mov eax, 1\n"
        assert data["duration_s"] == 0.5

    @patch("compiler.compile_source")
    def test_post_invalid_code_returns_errors(self, mock_compile, client):
        """POST com codigo invalido deve retornar erros."""
        from compiler import CompileResult

        mock_compile.return_value = CompileResult(
            success=False,
            nasm_output=None,
            binary_path=None,
            errors=[{"line": 5, "column": 10, "message": "comando invalido"}],
            duration_s=0.3,
            phases={},
        )

        response = client.post(
            "/api/compile",
            data=json.dumps({"code": "programa invalido"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
        assert data["errors"][0]["line"] == 5

    def test_post_without_code_returns_400(self, client):
        """POST sem campo 'code' deve retornar 400."""
        response = client.post(
            "/api/compile",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "code" in response.get_json()["error"]

    def test_post_without_body_returns_400(self, client):
        """POST sem body deve retornar 400."""
        response = client.post(
            "/api/compile",
            data=json.dumps(None),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_post_code_too_large_returns_413(self, client):
        """Codigo que excede o limite deve retornar 413."""
        large_code = "x" * (APP_CONFIG["max_code_kb"] * 1024 + 1)

        response = client.post(
            "/api/compile",
            data=json.dumps({"code": large_code}),
            content_type="application/json",
        )

        assert response.status_code == 413
        assert "limite" in response.get_json()["error"]
