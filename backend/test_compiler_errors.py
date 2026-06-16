"""
Testes do normalizador de erros de compilacao (compiler_errors.py).
"""

import json
import pytest
from compiler_errors import (
    normalize_error,
    normalize_errors,
    format_error_for_frontend,
    format_errors_for_frontend,
    _detect_phase,
    _classify_simplesc_error,
    _classify_nasm_error,
    _classify_ld_error,
    _parse_line_column,
    ERROR_CODES,
)


# ============================================================
# Testes: _detect_phase
# ============================================================

class TestDetectPhase:

    def test_detect_simplesc(self):
        """Erro com 'linha' deve ser detectado como simplesc."""
        assert _detect_phase("erro na linha 5: comando invalido") == "simplesc"

    def test_detect_nasm(self):
        """Erro com 'nasm:' deve ser detectado como nasm."""
        assert _detect_phase("nasm: error: parser: instruction expected") == "nasm"

    def test_detect_ld(self):
        """Erro com 'undefined reference' deve ser detectado como ld."""
        assert _detect_phase("undefined reference to `printf'") == "ld"

    def test_detect_default_simplesc(self):
        """Erro sem indicador claro deve ser detectado como simplesc (padrao)."""
        assert _detect_phase("erro desconhecido") == "simplesc"


# ============================================================
# Testes: _classify_simplesc_error
# ============================================================

class TestClassifySimplescError:

    def test_syntax_error(self):
        assert _classify_simplesc_error("erro de sintaxe") == "syntax"

    def test_unknown_command(self):
        assert _classify_simplesc_error("comando invalido") == "unknown_command"

    def test_unexpected_token(self):
        assert _classify_simplesc_error("token inesperado") == "unexpected_token"

    def test_missing_fim(self):
        assert _classify_simplesc_error("esperado 'fim'") == "missing_fim"

    def test_undeclared_variable(self):
        assert _classify_simplesc_error("variavel nao declarada") == "undeclared"

    def test_type_mismatch(self):
        assert _classify_simplesc_error("tipos incompativeis") == "type_mismatch"


# ============================================================
# Testes: _classify_nasm_error
# ============================================================

class TestClassifyNasmError:

    def test_parser_error(self):
        assert _classify_nasm_error("parser: instruction expected") == "parser"

    def test_label_error(self):
        assert _classify_nasm_error("label without colon") == "label"

    def test_instruction_error(self):
        assert _classify_nasm_error("instruction not supported") == "instruction"

    def test_operand_error(self):
        assert _classify_nasm_error("invalid operand type") == "operand"


# ============================================================
# Testes: _classify_ld_error
# ============================================================

class TestClassifyLdError:

    def test_undefined_reference(self):
        assert _classify_ld_error("undefined reference to `foo'") == "undefined_reference"

    def test_relocation_error(self):
        assert _classify_ld_error("relocation overflow") == "relocation"

    def test_segment_error(self):
        assert _classify_ld_error("segment `.text' exceeds") == "segment"

    def test_symbol_error(self):
        assert _classify_ld_error("undefined symbol: _start") == "undefined_reference"


# ============================================================
# Testes: _parse_line_column
# ============================================================

class TestParseLineColumn:

    def test_portuguese_format(self):
        """'linha 5, coluna 10'"""
        line, col = _parse_line_column("linha 5, coluna 10: comando invalido")
        assert line == 5
        assert col == 10

    def test_portuguese_format_line_only(self):
        """'linha 3' sem coluna"""
        line, col = _parse_line_column("linha 3: comando invalido")
        assert line == 3
        assert col == 0

    def test_gcc_like_format(self):
        """'arquivo:12:5: error:'"""
        line, col = _parse_line_column("source.simples:12:5: error: expected 'fim'")
        assert line == 12
        assert col == 5

    def test_no_match_returns_zero(self):
        """Sem correspondencia retorna (0, 0)."""
        line, col = _parse_line_column("erro generico")
        assert line == 0
        assert col == 0

    def test_english_format(self):
        """'line 7 column 3'"""
        line, col = _parse_line_column("line 7, column 3: unknown command")
        assert line == 7
        assert col == 3


# ============================================================
# Testes: normalize_error
# ============================================================

class TestNormalizeError:

    def test_normalize_simplesc_error(self):
        """Erro do simplesc deve ser normalizado com fase e codigo."""
        result = normalize_error(
            "linha 5, coluna 10: comando invalido",
            phase="simplesc",
        )

        assert result["phase"] == "simplesc"
        assert result["code"] == "E002"  # unknown_command
        assert result["line"] == 5
        assert result["column"] == 10
        assert result["severity"] == "error"
        assert "comando invalido" in result["message"]

    def test_normalize_nasm_error(self):
        """Erro do nasm deve ser normalizado com codigo N*."""
        result = normalize_error(
            "nasm: error: parser: instruction expected",
            phase="nasm",
        )

        assert result["phase"] == "nasm"
        assert result["code"] == "N002"  # parser
        assert result["severity"] == "error"

    def test_normalize_ld_error(self):
        """Erro do ld deve ser normalizado com codigo L*."""
        result = normalize_error(
            "undefined reference to `printf'",
            phase="ld",
        )

        assert result["phase"] == "ld"
        assert result["code"] == "L001"  # undefined_reference

    def test_normalize_with_auto_phase_detection(self):
        """Fase deve ser detectada automaticamente quando nao fornecida."""
        result = normalize_error(
            "nasm: error: parser: instruction expected",
        )

        assert result["phase"] == "nasm"

    def test_normalize_generic_error(self):
        """Erro generico deve usar codigo G001."""
        result = normalize_error(
            "erro desconhecido",
            phase="simplesc",
        )

        assert result["code"].startswith("E")

    def test_normalize_includes_raw_message(self):
        """Resultado deve incluir o raw original."""
        raw = "linha 5: comando invalido"
        result = normalize_error(raw, phase="simplesc")

        assert result["raw"] == raw


# ============================================================
# Testes: normalize_errors
# ============================================================

class TestNormalizeErrors:

    def test_normalize_multiline_string(self):
        """String com varias linhas deve gerar lista de erros."""
        errors = normalize_errors(
            "linha 3: comando invalido\nlinha 7: esperado 'fim'",
            phase="simplesc",
        )

        assert len(errors) == 2
        assert errors[0]["line"] == 3
        assert errors[1]["line"] == 7

    def test_normalize_list_of_strings(self):
        """Lista de strings deve ser processada."""
        errors = normalize_errors(
            ["linha 3: erro A", "linha 7: erro B"],
            phase="simplesc",
        )

        assert len(errors) == 2

    def test_empty_string_returns_empty_list(self):
        """String vazia retorna lista vazia."""
        errors = normalize_errors("", phase="simplesc")
        assert errors == []


# ============================================================
# Testes: format_error_for_frontend
# ============================================================

class TestFormatForFrontend:

    def test_format_error_to_monaco_marker(self):
        """Erro normalizado deve ser formatado para Monaco Marker."""
        normalized = {
            "phase": "simplesc",
            "code": "E001",
            "severity": "error",
            "line": 5,
            "column": 10,
            "message": "erro de sintaxe",
            "raw": "linha 5, coluna 10: erro de sintaxe",
        }

        marker = format_error_for_frontend(normalized)

        assert marker["startLineNumber"] == 5
        assert marker["startColumn"] == 10
        assert marker["endLineNumber"] == 5
        assert marker["endColumn"] == 11
        assert marker["severity"] == 8
        assert "[E001]" in marker["message"]

    def test_format_error_with_zero_column(self):
        """Erro sem coluna deve usar 1 como fallback."""
        normalized = {
            "phase": "simplesc",
            "code": "E001",
            "severity": "error",
            "line": 3,
            "column": 0,
            "message": "erro",
            "raw": "linha 3: erro",
        }

        marker = format_error_for_frontend(normalized)

        assert marker["startColumn"] == 1
        assert marker["endColumn"] == 2

    def test_format_errors_multiple(self):
        """Lista de erros deve ser formatada."""
        errors = [
            {"phase": "simplesc", "code": "E001", "severity": "error",
             "line": 5, "column": 10, "message": "erro A", "raw": "erro A"},
            {"phase": "nasm", "code": "N001", "severity": "error",
             "line": 0, "column": 0, "message": "erro B", "raw": "erro B"},
        ]

        markers = format_errors_for_frontend(errors)

        assert len(markers) == 2


# ============================================================
# Testes: ERROR_CODES completo
# ============================================================

class TestErrorCodes:

    def test_simplesc_has_expected_codes(self):
        """simplesc deve ter todos os codigos esperados."""
        expected = {"syntax", "unknown_command", "unexpected_token",
                    "missing_fim", "undeclared", "type_mismatch",
                    "invalid_expression"}
        assert set(ERROR_CODES["simplesc"].keys()) >= expected

    def test_nasm_has_expected_codes(self):
        """nasm deve ter todos os codigos esperados."""
        expected = {"syntax", "parser", "label", "instruction", "operand"}
        assert set(ERROR_CODES["nasm"].keys()) >= expected

    def test_ld_has_expected_codes(self):
        """ld deve ter todos os codigos esperados."""
        expected = {"undefined_reference", "relocation", "segment", "symbol"}
        assert set(ERROR_CODES["ld"].keys()) >= expected

    def test_all_codes_are_unique(self):
        """Todos os codigos de erro devem ser unicos."""
        all_codes = []
        for phase_codes in ERROR_CODES.values():
            all_codes.extend(phase_codes.values())

        assert len(all_codes) == len(set(all_codes)), "Codigos de erro duplicados"


# ============================================================
# Testes: integracao com endpoint /api/compile
# ============================================================

class TestIntegration:

    def test_normalize_then_format_roundtrip(self):
        """Erro normalizado e formatado deve preservar informacao essencial."""
        raw = "linha 5, coluna 10: comando invalido"

        normalized = normalize_error(raw, phase="simplesc")
        marker = format_error_for_frontend(normalized)

        # Verifica que a mensagem contem o codigo do erro
        assert "E002" in marker["message"]
        # Verifica que a posicao foi preservada
        assert marker["startLineNumber"] == 5
        assert marker["startColumn"] == 10

    def test_complete_pipeline_errors(self):
        """Cenario completo: erros das 3 fases."""
        simplesc_errors = normalize_errors(
            "linha 3: comando invalido\nlinha 7: esperado 'fim'",
            phase="simplesc",
        )
        nasm_errors = normalize_errors(
            "source.asm:15:10: error: parser: instruction expected",
            phase="nasm",
        )
        ld_errors = normalize_errors(
            "undefined reference to `_start'",
            phase="ld",
        )

        all_errors = simplesc_errors + nasm_errors + ld_errors

        assert len(all_errors) == 4
        assert all_errors[0]["phase"] == "simplesc"
        assert all_errors[2]["phase"] == "nasm"
        assert all_errors[3]["phase"] == "ld"

        # Formata para frontend
        markers = format_errors_for_frontend(all_errors)
        assert len(markers) == 4
