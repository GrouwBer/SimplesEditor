"""
Normalizacao de erros de compilacao por fase.

Padroniza mensagens de erro nas 3 fases do pipeline:
  - simplesc (SIMPLES → NASM)
  - nasm (NASM → .o)
  - ld (.o → ELF i686)

Formato normalizado:
    {
        "phase": "simplesc|nasm|ld",
        "code": "E001",
        "severity": "error|warning",
        "line": 5,
        "column": 10,
        "message": "descricao do erro",
        "raw": "mensagem original"
    }
"""

import re
from typing import Any


# Mapa de codigos de erro por fase
ERROR_CODES: dict[str, dict[str, str]] = {
    "simplesc": {
        "syntax": "E001",
        "unknown_command": "E002",
        "unexpected_token": "E003",
        "missing_fim": "E004",
        "undeclared": "E005",
        "type_mismatch": "E006",
        "invalid_expression": "E007",
    },
    "nasm": {
        "syntax": "N001",
        "parser": "N002",
        "label": "N003",
        "instruction": "N004",
        "operand": "N005",
    },
    "ld": {
        "undefined_reference": "L001",
        "relocation": "L002",
        "segment": "L003",
        "symbol": "L004",
    },
    "generic": {
        "unknown": "G001",
        "timeout": "G002",
        "not_found": "G003",
    },
}


def _classify_simplesc_error(message: str) -> str:
    """Classifica um erro do simplesc por tipo."""
    msg_lower = message.lower()
    if "sintax" in msg_lower or "syntax" in msg_lower:
        return "syntax"
    if "comando" in msg_lower and ("invalido" in msg_lower or "desconhec" in msg_lower):
        return "unknown_command"
    if "token" in msg_lower or "inesperad" in msg_lower:
        return "unexpected_token"
    if "fim" in msg_lower or "end" in msg_lower:
        return "missing_fim"
    if "declarad" in msg_lower or "definid" in msg_lower:
        return "undeclared"
    if "tipo" in msg_lower or "incompat" in msg_lower:
        return "type_mismatch"
    if "expressao" in msg_lower or "expressão" in msg_lower:
        return "invalid_expression"
    return "syntax"


def _classify_nasm_error(message: str) -> str:
    """Classifica um erro do nasm por tipo."""
    msg_lower = message.lower()
    if "parser" in msg_lower:
        return "parser"
    if "label" in msg_lower:
        return "label"
    if "instruction" in msg_lower or "mnemonic" in msg_lower:
        return "instruction"
    if "operand" in msg_lower or "register" in msg_lower:
        return "operand"
    return "syntax"


def _classify_ld_error(message: str) -> str:
    """Classifica um erro do ld por tipo."""
    msg_lower = message.lower()
    if "undefined reference" in msg_lower or "undefined symbol" in msg_lower:
        return "undefined_reference"
    if "relocation" in msg_lower:
        return "relocation"
    if "segment" in msg_lower or "section" in msg_lower:
        return "segment"
    if "symbol" in msg_lower:
        return "symbol"
    return "undefined_reference"


def _detect_phase(error_string: str) -> str:
    """Detecta de qual fase do pipeline veio o erro."""
    s_lower = error_string.lower()
    if any(x in s_lower for x in ["nasm:", "nasm ", "error: parser"]):
        return "nasm"
    if any(x in s_lower for x in ["ld: ", "undefined reference", "relocation"]):
        return "ld"
    if any(x in s_lower for x in ["simplesc", "linha", "escreva", "leia", "programa"]):
        return "simplesc"
    return "simplesc"  # padrao


def _parse_line_column(error_string: str) -> tuple[int, int]:
    """
    Extrai linha e coluna de uma mensagem de erro.

    Tenta varios formatos:
      - "linha 5, coluna 10: mensagem"
      - "source.simples:12:5: error:"
      - "file.asm:15:10: error:"
    """
    patterns = [
        r"(?:linha|line)\s*(\d+)(?:,\s*(?:coluna|column|col)\s*(\d+))?",
        r":(\d+):(\d+):",
        r"\[(?:linha|line)\s*(\d+)(?:,\s*coluna\s*(\d+))?\]",
    ]

    for pattern in patterns:
        m = re.search(pattern, error_string, re.IGNORECASE)
        if m:
            groups = m.groups()
            line = int(groups[0]) if groups[0] else 0
            column = int(groups[1]) if len(groups) > 1 and groups[1] else 0
            return line, column

    return 0, 0


def normalize_error(
    raw_error: str,
    phase: str | None = None,
) -> dict[str, Any]:
    """
    Normaliza uma mensagem de erro em formato padrao.

    Args:
        raw_error: Mensagem de erro crua.
        phase: Fase do pipeline (simplesc, nasm, ld).
               Se None, detecta automaticamente.

    Returns:
        Dict normalizado com phase, code, severity, line, column, message, raw.
    """
    if phase is None:
        phase = _detect_phase(raw_error)

    line, column = _parse_line_column(raw_error)

    if phase == "simplesc":
        error_type = _classify_simplesc_error(raw_error)
        code = ERROR_CODES["simplesc"].get(error_type, "E001")
    elif phase == "nasm":
        error_type = _classify_nasm_error(raw_error)
        code = ERROR_CODES["nasm"].get(error_type, "N001")
    elif phase == "ld":
        error_type = _classify_ld_error(raw_error)
        code = ERROR_CODES["ld"].get(error_type, "L001")
    else:
        code = ERROR_CODES["generic"]["unknown"]

    return {
        "phase": phase,
        "code": code,
        "severity": "error",
        "line": line,
        "column": column,
        "message": raw_error.strip(),
        "raw": raw_error.strip(),
    }


def normalize_errors(
    raw_errors: str | list[str],
    phase: str | None = None,
) -> list[dict[str, Any]]:
    """
    Normaliza multiplos erros.

    Args:
        raw_errors: String com multiplas linhas ou lista de strings.
        phase: Fase do pipeline. Se None, detecta por linha.

    Returns:
        Lista de erros normalizados.
    """
    if isinstance(raw_errors, str):
        lines = [line.strip() for line in raw_errors.split("\n") if line.strip()]
    else:
        lines = raw_errors

    return [normalize_error(line, phase) for line in lines]


def format_error_for_frontend(error: dict[str, Any]) -> dict[str, Any]:
    """
    Formata erro para consumo pelo frontend (Monaco markers).

    Retorna dict com:
      - message: string para exibicao
      - startLineNumber, startColumn: posicao no editor
      - endLineNumber, endColumn: posicao final (opcional)
      - severity: 8 = MarkerSeverity.Error (Monaco)
    """
    return {
        "message": f"[{error['code']}] {error['message']}",
        "startLineNumber": error["line"],
        "startColumn": error["column"] if error["column"] > 0 else 1,
        "endLineNumber": error["line"],
        "endColumn": (error["column"] + 1) if error["column"] > 0 else 2,
        "severity": 8,  # MarkerSeverity.Error
    }


def format_errors_for_frontend(
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Formata lista de erros para Monaco markers."""
    return [format_error_for_frontend(e) for e in errors]
