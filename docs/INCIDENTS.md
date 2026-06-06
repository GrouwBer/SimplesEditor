# Plano de Resposta a Incidentes

> Documento de referencia para resposta a incidentes de seguranca no SimplesEditor.
> Sprint 5 — Hardening & Observability (PRD secao 11.6, Threat model).

## Cenario 1: Aluno escapa do sandbox

**Vetor**: Binario compilado consegue acessar recursos fora do container sandbox.

**Mitigacoes ativas**:
- `--cap-drop=ALL`: Sem capabilities Linux (nao pode montar filesystems, usar raw sockets, etc.)
- `--security-opt=no-new-privileges`: Bloqueia escalacao de privilegios via setuid
- `--user=65534:65534` (nobody): Sem acesso root dentro do container
- `--network=none`: Sem rede para exfiltracao
- `--read-only`: Filesystem imutavel
- Seccomp profile padrao do Docker: Bloqueia syscalls perigosas (clone, mount, etc.)

**Resposta**:
1. **Deteccao**: Logs estruturados (JSON) mostrarao qualquer saida anomala do container. Monitore `/metrics` para `sandbox_escape_attempts_total`.
2. **Contencao imediata**: O container e destruido automaticamente ao fim da execucao (`--rm`). Se necessario, `docker kill` no container ativo.
3. **Investigacao**: Inspecione os logs do backend (`structlog`) filtrando pelo `user_id` e `execution_id`. Verifique o codigo submetido que causou o escape.
4. **Correcao**: Atualize o seccomp profile para bloquear a syscall especifica usada no escape. Atualize a imagem `simples-runner` se necessario.
5. **Prevencao**: Adicione teste de regressao em `scripts/audit_sandbox.sh` para o vetor especifico.

## Cenario 2: Fork bomb / DoS por consumo de recursos

**Vetor**: Programa SIMPLES gera muitos processos filhos (fork bomb) ou aloca memoria excessiva.

**Mitigacoes ativas**:
- `--pids-limit=64`: Maximo de 64 processos no container
- `--memory=128m --memory-swap=128m`: Limite rigido de memoria
- `--cpus=0.5`: Meia CPU, sem monopolizar o host

**Resposta**:
1. **Deteccao**: O Docker OOM Killer encerra o container automaticamente ao exceder 128 MB. Logs mostrarao `exit_code=137` (SIGKILL por OOM).
2. **Contencao**: Automatica — o container e removido apos timeout ou OOM.
3. **Investigacao**: Verifique o codigo submetido. Se for fork bomb intencional, considere reportar ao professor.
4. **Prevencao**: Ajuste `--pids-limit` e `--memory` se necessario. Monitore metricas `sandbox_oom_total`.

## Cenario 3: Exfiltracao de dados via codigo

**Vetor**: Aluno tenta enviar dados para servidor externo via syscalls de rede no codigo SIMPLES.

**Mitigacoes ativas**:
- `--network=none`: Container nao tem nenhuma interface de rede
- Syscalls de rede (`socket`, `connect`, `sendto`) sao bloqueadas pela falta de rede + seccomp

**Resposta**:
1. **Deteccao**: Chamadas de rede falham silenciosamente (errno apropriado). O aluno vera erro no terminal.
2. **Contencao**: Automatica — sem rede, sem exfiltracao possivel.
3. **Investigacao**: Nao necessario — o vetor e mitigado em 100% pelo `--network=none`.

## Cenario 4: Rate limit excedido (abuso de execucoes)

**Vetor**: Aluno ou atacante dispara mais de 30 execucoes/minuto.

**Mitigacoes ativas**:
- Rate limit de 30 execucoes/minuto por `user_id`
- Rate limit de 120 execucoes/minuto por IP

**Resposta**:
1. **Deteccao**: Backend retorna HTTP 429 `{error: "rate_limit_exceeded", retry_after_s: N}`.
2. **Contencao**: O rate limiter bloqueia automaticamente por 1 minuto.
3. **Investigacao**: Verifique logs de rate limiting (`structlog` event `rate_limit_hit`). Se for abuso intencional, considere bloquear o `user_id` temporariamente.
4. **Prevencao**: Ajuste os limites em `RUNS_PER_MINUTE` se necessario.

## Cenario 5: JWT comprometido

**Vetor**: Token JWT de um aluno e roubado (ex.: exposto em log, compartilhado acidentalmente).

**Mitigacoes ativas**:
- JWT expira em 1 hora (configuracao padrao Supabase)
- Backend valida JWT em toda conexao WebSocket e request REST
- Rate limit por user_id limita dano mesmo com token valido

**Resposta**:
1. **Deteccao**: Pico anormal de execucoes para um `user_id` especifico (detectavel via `/metrics`).
2. **Contencao**: O token expira automaticamente em 1h. Se urgente, revogue o token no Supabase Auth dashboard.
3. **Investigacao**: Verifique logs do backend filtrando pelo `user_id`. Identifique origem do vazamento (log exposto? compartilhamento?).
4. **Prevencao**: Eduque alunos sobre seguranca de tokens. Considere reduzir tempo de expiracao do JWT para 30 min.

## Contatos de Emergencia

| Papel | Contato |
|-------|---------|
| Maintainer do repositorio | @GrouwBer |
| Responsavel pela seguranca | @Jkvzin |
| Professor da disciplina | IFSULDEMINAS — Campus Pocos de Caldas |

## Procedimento de Notificacao

1. Abra uma issue no GitHub com label `security` e `incident`
2. Descreva: o que aconteceu, quando, qual user_id afetado, impacto
3. Se dados de outros alunos foram potencialmente expostos, notifique o professor imediatamente
4. Apos resolucao, documente o incidente neste arquivo na secao "Historico de Incidentes"

---

## Historico de Incidentes

| Data | Incidente | Severidade | Resolucao | Licao Aprendida |
|------|-----------|------------|-----------|-----------------|
| — | Nenhum incidente registrado | — | — | — |
