"""
Rotas de autenticacao (signup, signin, signout, me).

Usa o cliente Supabase para gerenciar usuarios.
Se o Supabase nao estiver configurado, retorna erros claros.
"""

from flask import Blueprint, jsonify, request

from config import (
    get_supabase_url,
    get_supabase_anon_key,
    get_supabase_jwt_secret,
    is_supabase_configured,
)
from dependencies import verify_jwt, get_current_user
from logging_config import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint("auth", __name__)


def _get_supabase_client():
    """Retorna cliente Supabase ou None se nao configurado."""
    if not is_supabase_configured():
        return None
    try:
        from supabase import create_client
        return create_client(get_supabase_url(), get_supabase_anon_key())
    except Exception as e:
        logger.error("supabase_client_error", error=str(e))
        return None


@auth_bp.route("/api/auth/signup", methods=["POST"])
def signup():
    """
    Cadastro de usuario.

    Request:
        {"email": "...", "password": "..."}

    Response (201):
        {"user": {...}, "session": {...}}

    Response (400):
        {"error": "..."}

    Response (503):
        {"error": "supabase_nao_configurado"}
    """
    data = request.get_json(silent=True)
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "email_e_senha_obrigatorios"}), 400

    email = data["email"]
    password = data["password"]

    if len(password) < 6:
        return jsonify({"error": "senha_deve_ter_no_minimo_6_caracteres"}), 400

    client = _get_supabase_client()
    if not client:
        return jsonify({"error": "supabase_nao_configurado"}), 503

    try:
        result = client.auth.sign_up({"email": email, "password": password})
        return jsonify({
            "user": {
                "id": result.user.id,
                "email": result.user.email,
            },
            "session": {
                "access_token": result.session.access_token
            } if result.session else None,
        }), 201
    except Exception as e:
        error_msg = str(e)
        logger.error("signup_error", error=error_msg)
        return jsonify({"error": error_msg}), 400


@auth_bp.route("/api/auth/signin", methods=["POST"])
def signin():
    """
    Login de usuario.

    Request:
        {"email": "...", "password": "..."}

    Response (200):
        {"user": {...}, "session": {"access_token": "...", ...}}
    """
    data = request.get_json(silent=True)
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "email_e_senha_obrigatorios"}), 400

    client = _get_supabase_client()
    if not client:
        return jsonify({"error": "supabase_nao_configurado"}), 503

    try:
        result = client.auth.sign_in_with_password({
            "email": data["email"],
            "password": data["password"],
        })
        return jsonify({
            "user": {
                "id": result.user.id,
                "email": result.user.email,
            },
            "session": {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": result.session.expires_in,
            },
        })
    except Exception as e:
        error_msg = str(e)
        logger.error("signin_error", error=error_msg)
        return jsonify({"error": "credenciais_invalidas"}), 401


@auth_bp.route("/api/auth/signout", methods=["POST"])
@verify_jwt
def signout():
    """
    Logout de usuario. Requer token valido.
    """
    client = _get_supabase_client()
    if not client:
        return jsonify({"error": "supabase_nao_configurado"}), 503

    try:
        client.auth.sign_out()
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error("signout_error", error=str(e))
        return jsonify({"error": "erro_ao_fazer_logout"}), 500


@auth_bp.route("/api/auth/me", methods=["GET"])
@verify_jwt
def me():
    """
    Retorna dados do usuario autenticado.
    """
    user = get_current_user()
    return jsonify(user)


@auth_bp.route("/api/auth/status", methods=["GET"])
def auth_status():
    """
    Verifica se o Supabase esta configurado.
    """
    return jsonify({
        "configured": is_supabase_configured(),
        "has_url": bool(get_supabase_url()),
        "has_anon_key": bool(get_supabase_anon_key()),
        "has_jwt_secret": bool(get_supabase_jwt_secret()),
    })
