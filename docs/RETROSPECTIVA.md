# Retrospectiva da Equipe — Simples Editor

**Sprint 6 — Polish & Deploy | Data: Junho 2026**

---

## O que aprendemos

### Tecnologias e Ferramentas

- **Docker e Docker Compose**: Aprendemos a orquestrar múltiplos serviços (nginx, frontend React, backend Flask, sandbox) com healthchecks, redes internas e volumes. A diferença entre imagens Alpine (sem curl/wget) e Ubuntu nos ensinou a projetar healthchecks compatíveis com cada base image.
- **GitHub Actions (CI/CD)**: Configuramos pipelines com jobs paralelos (frontend, backend, docker-stack, smoke tests). Aprendemos sobre `depends_on`, `needs`, e como depurar falhas de healthcheck em containers.
- **WebSocket + PTY**: Implementamos execução interativa de código SIMPLES com `flask-sock`, `gevent`, `xterm.js` e `docker-py`. A bridge bidirecional stdin/stdout via WebSocket foi o maior desafio técnico do projeto.
- **Segurança de Sandbox**: Configuramos `--cap-drop=ALL`, `--read-only`, `--network=none`, cgroups, rate limiting e timeouts. Entendemos na prática os riscos de execução de código arbitrário.
- **Monaco Editor**: Registramos uma linguagem customizada (SIMPLES) com tokenizer Monarch, tema dark e markers de erro. Aprendemos a API de extensibilidade do Monaco.

### Processos e Metodologia

- **Sprints e Kanban**: O GitHub Projects com issues, labels por sprint e assignees nos deu visibilidade contínua do progresso.
- **Code Review**: Revisões com "Changes Requested" nos forçaram a pensar em edge cases (healthchecks, compatibilidade Alpine vs Ubuntu, paths de build).
- **PR Flow**: O ciclo branch → commit → PR → review → CI → merge virou rotina. Aprendemos a resolver merge conflicts de forma sistemática.
- **Documentação**: Manter SPRINTS.md, README, e specs de design atualizados foi essencial para o paralelismo da equipe.

### Desafios Superados

1. **Healthcheck hell**: Containers Alpine não têm `curl` nem `wget`. Tivemos que usar `CMD-SHELL` com estratégias diferentes por imagem (curl no Ubuntu, wget no Alpine com busybox).
2. **Merge conflicts com reestruturação do CI**: Quando o `dev` separou o CI monolítico em jobs `frontend`/`backend`/`docker-stack`, o merge trouxe 7 conflitos simultâneos.
3. **Vite vs CRA**: O frontend usa Vite (porta 5173, output `dist/`), não Create React App (porta 3000, output `build/`). O compose override precisou de `target: builder` para o hot-reload.
4. **Linker i686**: Compilar código SIMPLES para 32-bit exigiu `binutils-i686-linux-gnu` e `nasm` no container.
5. **Rate limiting e segurança**: Balancear usabilidade (30 exec/min) com proteção contra abuso exigiu `flask-limiter` e métricas Prometheus.

---

## O que faríamos diferente

- **Testes desde o início**: Configurar pytest e ESLint na Sprint 1 evitaria a correria de corrigir CI na Sprint 6.
- **Healthchecks padronizados**: Definir uma estratégia única de healthcheck (ex: script customizado) em vez de depender de `curl`/`wget` específicos da imagem.
- **Docker registry**: Usar um registry (Docker Hub ou GHCR) para evitar rebuilds completos a cada CI run.
- **E2E tests mais cedo**: Playwright desde a Sprint 4 teria capturado regressões de UI antes da reta final.

---

## Pontos fortes da equipe

- **Colaboração assíncrona**: PRs bem documentados permitiram trabalho paralelo sem bloqueios.
- **Code review rigoroso**: Revisões com "Changes Requested" melhoraram a qualidade do código em cada iteração.
- **Resiliência**: Ninguém desistiu diante de falhas de CI repetidas — cada erro foi debugado sistematicamente.
- **Domínio full-stack**: A equipe saiu do projeto entendendo desde compiladores (NASM, linker) até deploy em cloud.

---

## Conclusão

O Simples Editor evoluiu de um skeleton docker-compose para uma plataforma completa de edição, compilação e execução interativa de código SIMPLES, com CI/CD, segurança de sandbox e observabilidade. O projeto está pronto para apresentação e deploy.

**Equipe**: GrouwBer, JoaoGarciaM, Jkvzin
