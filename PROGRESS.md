# PROGRESS.md — Simples Editor

> Acompanhamento de progresso das issues por sprint.

## Sprint 1 — Foundation & Auth
- [x] #4 chore(devops): definir docker-compose com nginx, frontend e backend
- [x] Repositório no GitHub criado, README inicial
- [x] GitHub Project (Kanban) configurado
- [x] Projeto Supabase criado, Auth configurado

## Sprint 2 — Editor & NASM Panel
- [x] Monaco Editor integrado
- [x] Linguagem custom `simples` registrada
- [x] Tema dark com keywords destacadas
- [x] Layout 3-painéis com splitter resizable

## Sprint 3 — Compilation Pipeline
- [x] simplesc empacotado no container backend
- [x] binutils-i686-linux-gnu instalado
- [x] Endpoint POST /api/compile
- [x] Erros renderizados como Monaco markers
- [x] NASM gerado popula painel direito

## Sprint 4 — Interactive Execution
- [x] WebSocket /ws/run com flask-sock + gevent
- [x] xterm.js integrado no painel terminal
- [x] Imagem simples-runner com qemu-user-static
- [x] Bridge bidirecional stdin/stdout
- [x] leia interativo funcional end-to-end

## Sprint 5 — Hardening & Observability
- [x] Rate limit (30 exec/min/user)
- [x] Logs estruturados JSON (structlog)
- [x] Métricas Prometheus em /metrics
- [x] Hard limit Docker configurado
- [x] #40 docs(docs): documentar resposta a incidente de sandbox
- [x] #38 chore(devops): expor metricas Prometheus
- [x] #37 chore(devops): adicionar logs estruturados em JSON
- [x] #34 chore(devops): configurar hard limit do container

## Sprint 6 — Polish & Deploy
- [x] #48 docs(docs): registrar retrospectiva da equipe
- [x] #47 docs(docs): preparar apresentacao final
- [ ] #46 feat(devops): configurar dominio proprio apontando para o deploy
- [ ] #45 feat(devops): publicar deploy em Oracle Cloud Ampere A1
- [ ] #44 docs(docs): add demo video
- [ ] #43 docs(docs): completar README com GIFs e screenshots
- [ ] Testes E2E com Playwright
- [ ] Cobertura de testes backend >= 70%
- [ ] Vídeo de demonstração (docs/demo.mp4)
