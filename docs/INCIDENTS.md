# Documentacao de Incidentes — Sandbox

> Procedimentos para resposta a incidentes de seguranca no sandbox do Simples Editor.

---

## Visao geral

O Simples Editor executa codigo de alunos em containers Docker isolados. Cada execucao roda em um container fresh com:

- `--cap-drop=ALL` — todas as capacidades do kernel removidas
- `--read-only` — filesystem somente leitura
- `--network=none` — sem acesso a rede
- `--memory=64m` — limite de memoria
- `--stop-timeout=12` — kill forcado apos timeout
- `--cpus=0.5` — limite de CPU
- Rate limit: 30 execucoes/minuto por usuario

---

## Classificacao de Incidentes

### Nivel 1 — Tentativa de Escape (BAIXO)

**Sintomas**:
- Log mostra tentativa de escrita em `/` (filesystem read-only)
- Erro: `Read-only file system`
- Tentativa de `fork()` ou `clone()`

**Resposta**:
1. Nao requer acao imediata — o sandbox bloqueia automaticamente
2. Registrar no log com `WARNING` e detalhes do usuario
3. Se o mesmo usuario repetir > 5 vezes em 1 hora, notificar administrador

### Nivel 2 — Consumo Excessivo de Recursos (MEDIO)

**Sintomas**:
- Timeout de execucao (10s wall-clock)
- Consumo de CPU > 80% por > 30s
- Memoria proxima do limite (64MB)

**Resposta**:
1. O rate limiter ja bloqueia apos 30 exec/min
2. Verificar se ha multiplos usuarios abusando simultaneamente
3. Ajustar `--memory` ou `--cpus` se necessario
4. Bloquear usuario temporariamente via Supabase Auth se abuso persistente

### Nivel 3 — Escape Bem-Sucedido (CRITICO)

**Sintomas**:
- Container conseguiu acessar rede externa
- Processo escapou do container (visivel no host)
- Acesso a arquivos fora do container
- Conexao de rede estabelecida para fora

**Resposta imediata**:
1. **Derrubar o servico**: `docker compose down`
2. **Isolar a VM**: desconectar da rede via console Oracle Cloud
3. **Coletar evidencias**:
   ```bash
   docker logs <container_id> > incident_$(date +%s).log
   journalctl -u docker --since "10 minutes ago" > docker_$(date +%s).log
   dmesg | tail -100 > dmesg_$(date +%s).log
   ```
4. **Analisar o payload**: qual codigo causou o escape?
5. **Corrigir a vulnerabilidade**: revisar configuracoes Docker, kernel
6. **Restaurar servico**: apos correcao, rebuild e redeploy
7. **Post-mortem**: documentar em `docs/INCIDENTS.md#historico`

### Nivel 4 — Comprometimento de Dados (CRITICO)

**Sintomas**:
- Acesso ao banco de dados Supabase nao autorizado
- Vazamento de `SUPABASE_JWT_SECRET` ou outras secrets
- Dados de usuarios acessados indevidamente

**Resposta imediata**:
1. **Rotacionar todas as secrets**: Supabase JWT, API keys, tokens
2. **Invalidar sessoes**: revogar todos os tokens JWT ativos
3. **Notificar usuarios afetados** (se aplicavel)
4. **Auditar logs** do Supabase para identificar escopo do vazamento
5. **Post-mortem** obrigatorio

---

## Monitoramento

### Metricas Prometheus (`/metrics`)

- `simples_executions_total` — total de execucoes
- `simples_execution_duration_seconds` — duracao das execucoes
- `simples_errors_total` — erros por tipo
- `simples_active_containers` — containers ativos

### Alertas recomendados

| Metrica | Limiar | Acao |
|---|---|---|
| `simples_errors_total{type="timeout"}` | > 10/min | Verificar abuso |
| `simples_active_containers` | > 20 | Possivel fork bomb |
| `simples_execution_duration_seconds` (p99) | > 8s | Ajustar timeout |

### Logs

Logs estruturados em JSON (structlog) incluem:
```json
{
  "event": "sandbox_exec",
  "user_id": "...",
  "container_id": "...",
  "duration_ms": 1234,
  "exit_code": 0,
  "level": "info",
  "timestamp": "..."
}
```

---

## Checklist de Resposta Rapida

- [ ] Identificar nivel do incidente (1-4)
- [ ] Coletar logs do container: `docker logs <id>`
- [ ] Coletar logs do sistema: `journalctl`, `dmesg`
- [ ] Verificar metricas Prometheus
- [ ] Bloquear usuario se necessario (Supabase Auth)
- [ ] Se nivel 3-4: `docker compose down` imediatamente
- [ ] Se nivel 3-4: rotacionar secrets
- [ ] Documentar no historico abaixo

---

## Historico de Incidentes

> Registrar cada incidente real com data, nivel, descricao e resolucao.

### Template

```markdown
### [DATA] — [TITULO]
- **Nivel**: [1-4]
- **Usuario**: [ID ou "anonimo"]
- **Descricao**: [O que aconteceu]
- **Payload**: [Codigo que causou o incidente]
- **Duracao**: [Tempo ate resolucao]
- **Resolucao**: [O que foi feito]
- **Licoes**: [O que aprendemos]
```

### Incidentes Registrados

*Nenhum incidente real registrado ate o momento. O sandbox tem bloqueado todas as tentativas de escape com sucesso.*
