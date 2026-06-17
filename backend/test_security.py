"""
Testes de seguranca do sandbox SimplesEditor.

Valida que as configuracoes de hardening definidas no PRD secao 11
estao corretamente aplicadas em sandbox_config.py e que
get_sandbox_run_kwargs() retorna os parametros esperados para o Docker SDK.
"""

from sandbox_config import (
    DOCKER_HARD_LIMITS,
    get_sandbox_run_kwargs,
    SANDBOX_CONFIG,
)


# ============================================================
# Testes: Filesystem read-only
# ============================================================

class TestFilesystemReadOnly:
    """PRD 11 — Layer 3: Filesystem read-only."""

    def test_read_only_enabled(self):
        """O container deve rodar com filesystem read-only."""
        assert DOCKER_HARD_LIMITS["read_only"] is True

    def test_tmpfs_configured(self):
        """Deve haver um tmpfs para /tmp com restricoes de seguranca."""
        tmpfs = DOCKER_HARD_LIMITS["tmpfs"]
        assert "/tmp" in tmpfs
        assert "noexec" in tmpfs["/tmp"], "/tmp deve ser noexec"
        assert "nosuid" in tmpfs["/tmp"], "/tmp deve ser nosuid"

    def test_tmpfs_size_limited(self):
        """O tmpfs deve ter limite de tamanho."""
        tmpfs = DOCKER_HARD_LIMITS["tmpfs"]
        assert "size=" in tmpfs["/tmp"], "/tmp deve ter limite de tamanho"

    def test_read_only_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir read_only."""
        kwargs = get_sandbox_run_kwargs()
        assert kwargs["read_only"] is True


# ============================================================
# Testes: Network isolation
# ============================================================

class TestNetworkIsolation:
    """PRD 11 — Layer 2: Network isolation."""

    def test_network_disabled(self):
        """O container deve ter rede desligada."""
        assert DOCKER_HARD_LIMITS["network_disabled"] is True

    def test_network_disabled_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir network_disabled=True."""
        kwargs = get_sandbox_run_kwargs()
        assert kwargs["network_disabled"] is True


# ============================================================
# Testes: Capabilities drop
# ============================================================

class TestCapabilitiesDrop:
    """PRD 11 — Layer 8: Capabilities dropped."""

    def test_cap_drop_all(self):
        """Todas as capabilities devem ser removidas (cap_drop: ALL)."""
        assert DOCKER_HARD_LIMITS["cap_drop"] == ["ALL"]

    def test_cap_drop_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir cap_drop com ALL."""
        kwargs = get_sandbox_run_kwargs()
        assert kwargs["cap_drop"] == ["ALL"]


# ============================================================
# Testes: Non-root user
# ============================================================

class TestNonRootUser:
    """PRD 11 — Layer 7: Non-root user."""

    def test_no_new_privileges(self):
        """O container deve ter no-new-privileges ativo."""
        assert "no-new-privileges" in DOCKER_HARD_LIMITS["security_opt"]

    def test_no_new_privileges_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir security_opt com no-new-privileges."""
        kwargs = get_sandbox_run_kwargs()
        assert "no-new-privileges" in kwargs["security_opt"]


# ============================================================
# Testes: PID limit (fork bomb prevention)
# ============================================================

class TestPidLimit:
    """PRD 11 — Layer 6: PID limit (fork bomb prevention)."""

    def test_pids_limit_configured(self):
        """Deve haver um limite de PIDs configurado."""
        assert DOCKER_HARD_LIMITS["pids_limit"] > 0

    def test_pids_limit_reasonable(self):
        """O limite de PIDs deve ser razoavel (64 ≤ n ≤ 256)."""
        pids = DOCKER_HARD_LIMITS["pids_limit"]
        assert 64 <= pids <= 256, (
            f"Limite de PIDs {pids} fora da faixa aceitavel (64-256)"
        )

    def test_pids_limit_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir pids_limit."""
        kwargs = get_sandbox_run_kwargs()
        assert kwargs["pids_limit"] == DOCKER_HARD_LIMITS["pids_limit"]


# ============================================================
# Testes: Memory limit
# ============================================================

class TestMemoryLimit:
    """PRD 11 — Layer 4: Memory limit."""

    def test_mem_limit_configured(self):
        """Deve haver um limite de memoria configurado."""
        mem = DOCKER_HARD_LIMITS["mem_limit"]
        assert mem is not None

    def test_mem_limit_reasonable(self):
        """O limite de memoria deve ser razoavel (32m ≤ n ≤ 512m)."""
        mem = str(DOCKER_HARD_LIMITS["mem_limit"])
        assert mem.endswith("m") or mem.endswith("g"), \
            "mem_limit deve usar sufixo m ou g"
        value = int(mem[:-1])
        # Aceita valores entre 32 MB e 512 MB
        suffix = mem[-1]
        if suffix == "m":
            assert 32 <= value <= 512, \
                f"mem_limit {mem} fora da faixa aceitavel (32m-512m)"
        elif suffix == "g":
            assert value <= 2, \
                f"mem_limit {mem} muito alto (max 2g)"

    def test_mem_limit_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir mem_limit."""
        kwargs = get_sandbox_run_kwargs()
        assert "mem_limit" in kwargs


# ============================================================
# Testes: CPU limit
# ============================================================

class TestCpuLimit:
    """PRD 11 — Layer 5: CPU limit."""

    def test_cpu_quota_configured(self):
        """Deve haver um CPU quota configurado."""
        quota = DOCKER_HARD_LIMITS["cpu_quota"]
        period = DOCKER_HARD_LIMITS["cpu_period"]
        assert quota > 0
        assert period > 0

    def test_cpu_quota_reasonable(self):
        """O CPU quota deve ser no maximo 1 core (quota ≤ period)."""
        quota = DOCKER_HARD_LIMITS["cpu_quota"]
        period = DOCKER_HARD_LIMITS["cpu_period"]
        assert quota <= period, (
            f"CPU quota {quota} excede o period {period} (max 1 core)"
        )

    def test_cpu_quota_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir cpu_quota e cpu_period."""
        kwargs = get_sandbox_run_kwargs()
        assert "cpu_quota" in kwargs
        assert "cpu_period" in kwargs


# ============================================================
# Testes: Stop timeout
# ============================================================

class TestStopTimeout:
    """PRD 11 — Container stop timeout."""

    def test_stop_timeout_configured(self):
        """Deve haver um stop timeout configurado (SIGTERM → SIGKILL)."""
        timeout = DOCKER_HARD_LIMITS["stop_timeout"]
        assert timeout > 0, "stop_timeout deve ser positivo"
        assert timeout <= 30, "stop_timeout nao deve exceder 30s"

    def test_stop_timeout_in_run_kwargs(self):
        """get_sandbox_run_kwargs deve incluir stop_timeout."""
        kwargs = get_sandbox_run_kwargs()
        assert "stop_timeout" in kwargs


# ============================================================
# Testes: Defense in depth — todas as camadas presentes
# ============================================================

class TestDefenseInDepth:
    """PRD 11 — Todas as camadas de defense in depth devem estar presentes."""

    # Camadas esperadas conforme PRD secao 11
    EXPECTED_LAYERS = {
        "read_only": "Layer 3: Filesystem read-only",
        "network_disabled": "Layer 2: Network isolation",
        "cap_drop": "Layer 8: Capabilities dropped",
        "pids_limit": "Layer 6: PID limit (fork bomb)",
        "mem_limit": "Layer 4: Memory limit",
        "cpu_quota": "Layer 5: CPU limit",
        "stop_timeout": "Container stop timeout",
        "security_opt": "Layer 9: no-new-privileges",
    }

    def test_all_security_keys_present_in_run_kwargs(self):
        """Todas as camadas de seguranca devem estar em get_sandbox_run_kwargs()."""
        kwargs = get_sandbox_run_kwargs()
        for key, description in self.EXPECTED_LAYERS.items():
            assert key in kwargs, (
                f"{description}: chave '{key}' ausente em get_sandbox_run_kwargs()"
            )

    def test_sandbox_config_includes_all(self):
        """SANDBOX_CONFIG deve conter todas as configuracoes de seguranca."""
        for key in self.EXPECTED_LAYERS:
            assert key in SANDBOX_CONFIG, (
                f"Chave de seguranca '{key}' ausente em SANDBOX_CONFIG"
            )

    def test_dockerfile_labels_present(self):
        """Verifica se o runner/Dockerfile tem os labels de seguranca esperados."""
        import os
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "runner", "Dockerfile"
        )
        dockerfile_path = os.path.normpath(dockerfile_path)

        assert os.path.exists(dockerfile_path), \
            f"runner/Dockerfile nao encontrado em {dockerfile_path}"

        with open(dockerfile_path) as f:
            content = f.read()

        # Verifica labels de seguranca
        assert "org.simples-editor.security.read_only" in content
        assert "org.simples-editor.security.network" in content
        assert "org.simples-editor.security.user" in content
        assert "nobody" in content


# ============================================================
# Testes: Runner Dockerfile hardening
# ============================================================

class TestRunnerDockerfile:
    """Valida que o runner/Dockerfile segue as praticas de hardening."""

    def test_uses_slim_base_image(self):
        """O Dockerfile deve usar uma imagem base enxuta (slim)."""
        import os
        dockerfile_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "runner", "Dockerfile")
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "debian:12-slim" in content, \
            "Deve usar debian:12-slim como base"

    def test_non_root_user(self):
        """O Dockerfile deve criar e usar um usuario nao-root."""
        import os
        dockerfile_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "runner", "Dockerfile")
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "USER" in content, \
            "Deve ter um USER statement"
        assert "65534" in content or "nobody" in content, \
            "Deve usar UID 65534 (nobody)"

    def test_removes_unnecessary_binaries(self):
        """O Dockerfile deve remover binarios desnecessarios."""
        import os
        dockerfile_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "runner", "Dockerfile")
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "find /usr/bin" in content or "rm -rf" in content, \
            "Deve remover binarios desnecessarios"

    def test_security_labels_present(self):
        """O Dockerfile deve conter labels de seguranca."""
        import os
        dockerfile_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "runner", "Dockerfile")
        )
        with open(dockerfile_path) as f:
            content = f.read()
        assert "LABEL" in content, \
            "Deve ter secao de LABELs"
        assert "org.simples-editor.sandbox" in content
