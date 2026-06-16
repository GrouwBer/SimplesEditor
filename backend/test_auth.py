"""
Testes de autenticacao (auth, dependencies, config).
"""

import json
from unittest.mock import MagicMock, patch, ANY

import pytest
from app import app


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================================
# Testes: config
# ============================================================

class TestConfig:

    def test_is_not_configured_by_default(self):
        """Sem env vars, Supabase nao deve estar configurado."""
        from config import is_supabase_configured
        assert is_supabase_configured() is False

    def test_is_configured_with_env_vars(self, monkeypatch):
        """Com env vars, deve estar configurado."""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-jwt-secret")

        # Recarrega o modulo para pegar as novas env vars
        import config
        import importlib
        importlib.reload(config)

        assert config.is_supabase_configured() is True


# ============================================================
# Testes: verify_jwt
# ============================================================

class TestVerifyJwt:

    def test_missing_auth_header(self, client):
        """Request sem Authorization deve retornar 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "token_ausente" in response.get_json()["error"]

    def test_invalid_auth_header(self, client):
        """Header sem Bearer deve retornar 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Invalid token"},
        )
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Token invalido deve retornar 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401

    @patch("dependencies.jwt.decode")
    def test_valid_token(self, mock_decode, client, monkeypatch):
        """Token valido deve retornar dados do usuario."""
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")

        import config
        import importlib
        importlib.reload(config)

        mock_decode.return_value = {
            "sub": "user-123",
            "email": "aluno@test.com",
            "user_metadata": {"name": "Aluno Teste"},
        }

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer valid.token.here"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_id"] == "user-123"
        assert data["email"] == "aluno@test.com"


# ============================================================
# Testes: /api/auth/status
# ============================================================

class TestAuthStatus:

    def test_status_unconfigured(self, client):
        """Sem configuracao, status deve indicar nao configurado."""
        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["configured"] is False

    def test_status_configured(self, client, monkeypatch):
        """Com configuracao, status deve indicar configurado."""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")

        import config
        import importlib
        importlib.reload(config)

        response = client.get("/api/auth/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["configured"] is True


# ============================================================
# Testes: /api/auth/signup
# ============================================================

class TestSignup:

    def test_missing_fields(self, client):
        """Signup sem email/senha deve retornar 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_short_password(self, client):
        """Senha muito curta deve retornar 400."""
        response = client.post(
            "/api/auth/signup",
            data=json.dumps({"email": "test@test.com", "password": "123"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_supabase_not_configured(self, client, monkeypatch):
        """Sem configuracao Supabase, deve retornar 503."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
        monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

        import config
        import importlib
        importlib.reload(config)

        response = client.post(
            "/api/auth/signup",
            data=json.dumps({"email": "test@test.com", "password": "123456"}),
            content_type="application/json",
        )
        assert response.status_code == 503
        assert "supabase_nao_configurado" in response.get_json()["error"]


# ============================================================
# Testes: /api/auth/signin
# ============================================================

class TestSignin:

    def test_missing_fields(self, client):
        """Signin sem campos deve retornar 400."""
        response = client.post(
            "/api/auth/signin",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400


# ============================================================
# Testes: /api/auth/signout
# ============================================================

class TestSignout:

    def test_requires_auth(self, client):
        """Signout sem token deve retornar 401."""
        response = client.post("/api/auth/signout")
        assert response.status_code == 401
