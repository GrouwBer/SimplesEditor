# SPRINTS

## Sprint 1 — Foundation & Auth
# SPRINTS

**Objetivo**: Estrutura mínima funcional para todos os integrantes começarem a trabalhar em paralelo.

**Entregáveis**:

- [ ]  Repositório no GitHub criado, README inicial
- [ ]  GitHub Project (Kanban) configurado com colunas e automações
- [ ]  `docker-compose.yml` com 3 serviços: nginx, frontend (skeleton React), backend (skeleton Flask)
- [ ]  `docker compose up` levanta tudo, página inicial responde em http://localhost
- [ ]  Projeto Supabase criado, Auth configurado
- [ ]  Frontend tem tela de login funcionando (email/senha)
- [ ]  Backend tem decorator `@verify_jwt` validando token nos endpoints
- [ ]  Endpoint `/api/health` retorna `{status: "ok"}`
- [ ]  Pelo menos 1 PR mergeado por integrante (rodagem do fluxo)

**Definition of Done**: aluno consegue clonar o repo, rodar `docker compose up`, fazer login, ver health check verde.

## Sprint 2 — Editor & NASM Panel

**Objetivo**: UI principal pronta, ainda sem backend de compilação.

**Entregáveis**:

- [ ]  Monaco Editor integrado na rota principal
- [ ]  Linguagem custom `simples` registrada com tokenizer Monarch (27 keywords)
- [ ]  Tema dark com keywords destacadas
- [ ]  Layout 3-painéis: editor (esq.), painel NASM (dir.), terminal (inferior — placeholder)
- [ ]  Splitter resizable entre editor e NASM (`react-resizable-panels`), double-click colapsa
- [ ]  Botão **Run** (mockado — apenas mostra "compilando…")
- [ ]  Painel NASM read-only com seu próprio Monaco em modo `asm`

**Definition of Done**: aluno consegue digitar código SIMPLES, ver highlighting correto, redimensionar painéis. Botão Run não faz nada ainda.

## Sprint 3 — Compilation Pipeline

**Objetivo**: Pipeline `simplesc → nasm → ld` funcional via REST (sem WebSocket ainda).

**Entregáveis**:

- [ ]  `simplesc` empacotado no container backend (multi-stage Dockerfile)
- [ ]  `binutils-i686-linux-gnu` instalado, linker funciona
- [ ]  Endpoint `POST /api/compile` aceita código, retorna NASM ou erros
- [ ]  Erros parseados em `{line, column, message}` por fase (lexer/parser/semantic)
- [ ]  Frontend renderiza erros como **Monaco markers** (linha vermelha sublinhada)
- [ ]  NASM gerado popula painel direito automaticamente
- [ ]  Timeouts de compilação (15s) implementados

**Definition of Done**: aluno escreve programa SIMPLES válido, clica Run, vê NASM no painel direito. Programa inválido mostra linha do erro.

## Sprint 4 — Interactive Execution

**Objetivo**: O coração do projeto. WebSocket + PTY + xterm.js + sandbox.

**Entregáveis**:

- [ ]  WebSocket `/ws/run` no backend (flask-sock + gevent worker)
- [ ]  xterm.js integrado no painel terminal do frontend
- [ ]  Imagem `simples-runner` com `qemu-user-static`
- [ ]  `PtyExecutionStrategy` implementada (docker-py + `attach_socket`)
- [ ]  Bridge bidirecional: stdout/stderr → ws → xterm.js; xterm.js input → ws → pty
- [ ]  `leia` interativo funciona end-to-end (programa pede número, usuário digita, programa continua)
- [ ]  Mensagens do protocolo WS implementadas (`compile_started`, `asm_generated`, `exec_started`, `stdout`, `stdin`, `exit`)

**Definition of Done**: aluno escreve programa que faz `leia x; escreva x`, roda, é solicitado a digitar, digita, vê valor de volta no terminal.

## Sprint 5 — Hardening & Observability

**Objetivo**: Production-ready. Não cai sob carga, não vaza, observável.

**Entregáveis**:

- [ ]  Botão **Stop** funcional (envia `{type: "stop"}` → SIGTERM → SIGKILL)
- [ ]  Timeout de execução wall-clock (10s) com `asyncio.wait_for`
- [ ]  Hard limit Docker (`--stop-timeout=12`)
- [ ]  `--cap-drop=ALL`, `--read-only`, `--network=none`, cgroups configurados
- [ ]  Rate limit (30 execuções/min/user) com `flask-limiter`
- [ ]  Logs estruturados JSON (`structlog`)
- [ ]  Métricas Prometheus em `/metrics` (interno apenas)
- [ ]  Audit do sandbox: tentativa de escrever em `/`, fork bomb, network — todas bloqueadas
- [ ]  Documentação de incidente (`docs/INCIDENTS.md`) — o que fazer se um aluno escapar

**Definition of Done**: code review de segurança feito por outro grupo. Loop infinito é interrompido em ≤11s. Stop interrompe em ≤2s.

## Sprint 6 — Polish & (Opcional) Deploy

**Objetivo**: Apresentável. Documentado. Pronto pra publicar.

**Entregáveis**:

- [ ]  Testes E2E com Playwright (login, edit, run, stdin, stop, timeout)
- [ ]  Cobertura de testes backend ≥ 70% (`pytest --cov`)
- [x]  [README.md](http://README.md) completo com GIFs/screenshots
- [ ]  Vídeo de demonstração de 2-3 min (`docs/demo.mp4`)
- [ ]  **(Opcional, +1.0 ponto)** Deploy em Oracle Cloud Ampere A1 com TLS válido
- [ ]  **(Opcional)** Domínio próprio (`*.edu.br`) apontando pro IP
- [ ]  Apresentação final preparada (slides ou Notion)
- [x]  Retrospectiva da equipe (o que aprendemos)
## Sprint 1 - Foundation & Auth
- Estruturar repositório no GitHub e README inicial
- Exercitar fluxo de PR
