"""
Dependencias para autenticacao via Supabase JWT.

Fornece o decorator verify_jwt que protege endpoints Flask.
O JWT e extraido do header Authorization: Bearer <token>
e validado contra o JWT secret do Supabase.
"""

from functools import wraps
from typing import Any, Callable

import jwt
from flask import request, jsonify, g

from config import get_supabase_jwt_secret, is_supabase_configured


class AuthError(Exception):
    """Erro de autenticacao."""
    pass


def verify_jwt(f: Callable) -> Callable:
    """
    Decorator que verifica o JWT do Supabase no request.

    Extrai o token do header Authorization: Bearer <token>,
    valida a assinatura com o JWT secret do Supabase,
    e injeta g.user_id e g.user_email no contexto do Flask.

    Uso:
        @app.route('/api/protected')
        @verify_jwt
        def protected_route():
            return jsonify({"user_id": g.user_id})
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "token_ausente"}), 401

        token = auth_header[7:].strip()  # Remove "Bearer "
        if not token:
            return jsonify({"error": "token_ausente"}), 401

        try:
            payload = _validate_token(token)
            g.user_id = payload.get("sub")
            g.user_email = payload.get("email", "")
            g.user_metadata = payload.get("user_metadata", {})

        except AuthError as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            return jsonify({"error": "token_invalido"}), 401

        return f(*args, **kwargs)

    return decorated


def _validate_token(token: str) -> dict:
    """
    Valida o JWT token.
    """
    secret = get_supabase_jwt_secret()

    if not secret or not is_supabase_configured():
        raise AuthError("supabase_nao_configurado")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("token_expirado")
    except jwt.InvalidTokenError:
        raise AuthError("token_invalido")


def get_current_user() -> dict:
    """
    Retorna dados do usuario autenticado no request atual.
    Deve ser chamado apos verify_jwt.
    """
    return {
        "user_id": g.get("user_id"),
        "email": g.get("user_email", ""),
        "metadata": g.get("user_metadata", {}),
    }
