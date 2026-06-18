# PROGRESS.md — Simples Editor

> Acompanhamento de progresso das issues por sprint.
> Itens concluidos sao marcados com [x].

## Sprint 1 — Foundation & Auth
- [x] #4 chore(devops): definir docker-compose com nginx, frontend e backend
- [x] Repositorio no GitHub criado, README inicial
- [x] GitHub Project (Kanban) configurado
- [x] docker-compose.yml com 3 servicos
- [x] Projeto Supabase criado, Auth configurado
- [x] Endpoint /api/health retorna {status: "ok"}

## Sprint 2 — Editor & NASM Panel
- [x] Monaco Editor integrado
- [x] Linguagem custom `simples` registrada (Monarch tokenizer)
- [x] Tema dark com keywords destacadas
- [x] Layout 3-paineis com splitter resizable
- [x] Botao Run mockado (removido — substituido por WebSocket real)

## Sprint 3 — Compilation Pipeline
- [x] simplesc empacotado no container backend
- [x] binutils-i686-linux-gnu instalado, linker funcional
- [x] Endpoint POST /api/compile
- [x] Erros renderizados como Monaco markers
- [x] NASM gerado popula painel direito

## Sprint 4 — Interactive Execution
- [x] WebSocket /ws/run com flask-sock + gevent
- [x] xterm.js integrado no painel terminal
- [x] Imagem simples-runner com qemu-user-static
- [x] PtyExecutionStrategy com docker-py
- [x] Bridge bidirecional stdin/stdout
- [x] leia interativo funcional end-to-end

## Sprint 5 — Hardening & Observability
- [x] Rate limit (30 exec/min/user)
- [x] Logs estruturados JSON (structlog)
- [x] Metricas Prometheus em /metrics
- [x] Hard limit Docker configurado
- [x] Sandbox security (cap-drop, read-only, network=none)
- [x] #40 docs(docs): documentar resposta a incidente de sandbox
- [x] #38 chore(devops): expor metricas Prometheus em /metrics
- [x] #37 chore(devops): adicionar logs estruturados em JSON
- [x] #34 chore(devops): configurar hard limit do container

## Sprint 6 — Polish & Deploy
- [x] #48 docs(docs): registrar retrospectiva da equipe
- [x] #47 docs(docs): preparar apresentacao final
- [x] #46 feat(devops): configurar dominio proprio apontando para o deploy
- [x] #45 feat(devops): publicar deploy em Oracle Cloud Ampere A1
- [x] #44 docs(docs): add demo video
- [x] #43 docs(docs): completar README com GIFs e screenshots
- [x] Testes E2E com Playwright (#41)
- [x] Cobertura de testes backend >= 70% (#42)

## Pendente
- [ ] #106 test(e2e): converter testes placeholder em testes reais
- [ ] Push secrets no GitHub para deploy automatizado
- [ ] Merge dev → main para disparar deploy via CI
