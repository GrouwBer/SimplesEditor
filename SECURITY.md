# Security

> **Última revisão:** 2026-06-15

## Politica de Segredos

Do NOT commit secrets (API keys, tokens, passwords) in this repository.
If you find a secret accidentally committed, notify the maintainers immediately and rotate the secret.

To report a security vulnerability, open an issue with the label `security` or contact the maintainers directly.

## Sandbox Hardening (9 Camadas de Defesa)

O sandbox de execucao (`simples-runner`) implementa defense-in-depth conforme PRD secao 11:

| Camada | Mecanismo | Configuracao | Objetivo |
|--------|-----------|-------------|----------|
| 1 | Container descartavel | `docker run --rm` | Container destruido apos execucao |
| 2 | Network isolation | `--network=none` | Sem qualquer acesso a rede |
| 3 | Filesystem | `--read-only` + `tmpfs:/tmp,size=8m,noexec` | FS imutavel, /tmp em RAM limitado |
| 4 | Memoria | `--memory=128m --memory-swap=128m` | Sem swap, OOM kill rapido |
| 5 | CPU | `--cpus=0.5` | Meia CPU, sem monopolizar host |
| 6 | PIDs | `--pids-limit=64` | Bloqueia fork bomb |
| 7 | Usuario | `--user=65534:65534` (nobody) | Nao-root dentro do container |
| 8 | Capabilities | `--cap-drop=ALL` | Sem capabilities Linux |
| 9 | Seccomp + no-new-privileges | `--security-opt=no-new-privileges` | Bloqueia escalacao de privilegios |

### Auditoria de Seguranca

Para validar o hardening do sandbox, execute:

```bash
# Build da imagem do sandbox
docker compose build runner_image_build

# Executar auditoria de seguranca
bash scripts/audit_sandbox.sh
```

O script verifica todos os 7 vetores testaveis:
- [x] Filesystem read-only
- [x] Network isolation
- [x] PIDs limit (fork bomb)
- [x] Capabilities drop
- [x] Non-root user
- [x] Memory limit
- [x] No-new-privileges

### Resposta a Incidentes

Consulte [docs/INCIDENTS.md](docs/INCIDENTS.md) para o plano completo de resposta a incidentes de seguranca.

## Threat Model (Resumo)

| Ameaca | Mitigacao |
|--------|-----------|
| Loop infinito | Wall-clock timeout (10s) |
| Fork bomb | `--pids-limit=64` |
| Memoria ilimitada | `--memory=128m` |
| Exfiltracao via rede | `--network=none` |
| Escape do container | Non-root + `--cap-drop=ALL` + seccomp |
| Abuso de execucoes | Rate limit por user e IP (30/min) |
| JWT roubado | Expiracao curta (1h padrao Supabase) |
| Code injection no shell | Backend usa `subprocess` com lista de args, nunca `shell=True` |
