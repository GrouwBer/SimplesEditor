# Simples Runner — Sandbox de execucao descartavel
# Imagem minima para executar binarios x86 32-bit (SIMPLES → NASM → ld)
# com qemu-user-static para emulacao em hosts ARM64.
#
# Hardening aplicado (defense in depth — PRD secao 11):
#   Layer 1: Container descartavel (docker run --rm)
#   Layer 2: Network isolation (--network=none)
#   Layer 3: Filesystem read-only (--read-only + tmpfs:/tmp)
#   Layer 4: Memory limit (--memory=128m --memory-swap=128m)
#   Layer 5: CPU limit (--cpus=0.5)
#   Layer 6: PID limit (--pids-limit=64) — bloqueia fork bomb
#   Layer 7: Non-root user (--user=65534:65534)
#   Layer 8: Capabilities dropped (--cap-drop=ALL)
#   Layer 9: Seccomp profile (Docker default)
#
# NOTA: As politicas de hardening nos layers 2-9 sao aplicadas
# pelo backend via Docker SDK no momento do spawn. Este Dockerfile
# garante que a imagem em si nao tem superficies de ataque desnecessarias.

FROM debian:12-slim

# Instala apenas o essencial: qemu-user-static para emulacao i386
# Nenhum shell interativo, compilador ou ferramenta de rede
RUN apt-get update && apt-get install -y --no-install-recommends \
      qemu-user-static \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Cria usuario sandbox sem shell, sem home, sem login
# UID/GID 65534 = nobody (padrao sistemas Linux)
RUN useradd -u 65534 -M -s /usr/sbin/nologin sandbox || true

# Remove binarios desnecessarios para reduzir superficie de ataque
# Mantem apenas /usr/bin/qemu-i386-static
RUN find /usr/bin -type f ! -name 'qemu-i386-static' -delete 2>/dev/null || true \
    && find /usr/sbin -type f -delete 2>/dev/null || true \
    && find /bin -type f -delete 2>/dev/null || true \
    && find /sbin -type f -delete 2>/dev/null || true

# Diretorio de trabalho — montado como read-only bind mount pelo backend
# O binario compilado e colocado aqui pelo backend antes do container iniciar
RUN mkdir -p /sandbox && chown 65534:65534 /sandbox

# Metadata de seguranca
LABEL org.simples-editor.sandbox="true" \
      org.simples-editor.version="1.0" \
      org.simples-editor.security.read_only="true" \
      org.simples-editor.security.network="none" \
      org.simples-editor.security.user="nobody"

# Executa como nobody (UID 65534)
USER 65534:65534

WORKDIR /sandbox

# Entrypoint: executa o binario via qemu-user-static
# O caminho do binario e passado como argumento pelo backend
ENTRYPOINT ["/usr/bin/qemu-i386-static"]
