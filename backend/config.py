"""
Configuracao do Supabase para autenticacao.

As variaveis de ambiente sao carregadas do .env ou docker-compose.
"""

import os


def get_supabase_url() -> str:
    """Retorna a URL do projeto Supabase."""
    return os.environ.get("SUPABASE_URL", "")


def get_supabase_anon_key() -> str:
    """Retorna a chave anonima do Supabase."""
    return os.environ.get("SUPABASE_ANON_KEY", "")


def get_supabase_jwt_secret() -> str:
    """Retorna o JWT secret do Supabase."""
    return os.environ.get("SUPABASE_JWT_SECRET", "")


def is_supabase_configured() -> bool:
    """Verifica se todas as credenciais Supabase estao configuradas."""
    return all([get_supabase_url(), get_supabase_anon_key(), get_supabase_jwt_secret()])
