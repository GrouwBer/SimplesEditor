# PRD — Simples Editor (Web IDE)

> **Product Requirements Document** — Web IDE para a linguagem **SIMPLES**
> IFSULDEMINAS — Campus Poços de Caldas — Disciplina de Compiladores
> Versão: 1.0 (rascunho) · Última atualização: 2026-05-05

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Contexto e premissas](#2-contexto-e-premissas)
3. [Personas e user stories](#3-personas-e-user-stories)
4. [Escopo](#4-escopo)
5. [Requisitos funcionais](#5-requisitos-funcionais)
6. [Requisitos não-funcionais](#6-requisitos-não-funcionais)
7. [Arquitetura](#7-arquitetura)
8. [Stack técnica](#8-stack-técnica)
9. [API design — REST + WebSocket](#9-api-design--rest--websocket)
10. [Modelo de dados (Supabase)](#10-modelo-de-dados-supabase)
11. [Segurança e sandboxing](#11-segurança-e-sandboxing)
12. [UI/UX](#12-uiux)
13. [Editor de código (Monaco)](#13-editor-de-código-monaco)
14. [Docker Compose](#14-docker-compose)
15. [Nginx — reverse proxy](#15-nginx--reverse-proxy)
16. [Observabilidade](#16-observabilidade)
17. [Estratégia de testes](#17-estratégia-de-testes)
18. [Roadmap](#18-roadmap)
19. [Riscos e mitigações](#19-riscos-e-mitigações)
20. [Critérios de aceite](#20-critérios-de-aceite)
21. [Apêndices](#21-apêndices)

---

## 1. Visão geral

**Simples Editor** é uma IDE web que permite ao aluno escrever, compilar e executar programas na linguagem **SIMPLES** diretamente no navegador, sem nenhuma instalação local. O ambiente expõe três painéis simultâneos:

- **Editor SIMPLES** (esquerda): code editor com syntax highlighting das 27 palavras reservadas da linguagem.
- **Painel NASM x32** (direita, expansível/contrátil): mostra o assembly gerado pelo compilador `simplesc`, lado-a-lado com o código fonte.
- **Terminal** (inferior): emulador de terminal real (xterm.js) conectado por WebSocket ao processo executado no servidor — suporta `leia` (stdin) e `escreva` (stdout) de forma interativa, igual a um terminal local.

Toda a stack roda containerizada (Docker Compose) e fica atrás de um Nginx como reverse proxy. Autenticação via Supabase. O compilador `simplesc` (já existente, escrito em C, descrito no [PRD do compilador](https://www.notion.so/344a6259575b81098b28f3235354d86b)) é invocado pelo backend Flask, que orquestra o pipeline completo: `simplesc → nasm → ld → execução em sandbox`.

> **Analogia:** o sistema funciona como uma **cozinha industrial com vidro**. O aluno (cliente) escolhe um prato no cardápio (o código SIMPLES). A cozinha (o backend) prepara em três etapas — cortar (compilar), cozinhar (montar/linkar), empratar (executar) — tudo isolado por uma porta de vidro (o Docker sandbox). O cliente vê em tempo real, pelo vidro, o que está acontecendo (saída no terminal), pode interagir (passar sal pela janela = `leia`), e nunca encosta no fogão.

---

## 2. Contexto e premissas

### 2.1 Contexto educacional

A disciplina de **Compiladores** do curso de Engenharia de Computação produz, ao longo do semestre, um compilador funcional para a linguagem SIMPLES — uma linguagem didática em português estruturado (`programa`, `inicio`, `fim`, `leia`, `escreva`, `enquanto`, `para`, `se/entao/senao`). O compilador `simplesc` traduz SIMPLES → NASM x86 32-bit, e o aluno hoje precisa rodar `nasm`, `ld` e o binário em um Linux 32-bit local. Essa fricção desestimula a prática.

A IDE web elimina essa fricção: o aluno acessa, autentica, escreve e roda. O foco didático é **ver o que cada construção SIMPLES vira em assembly** e **executar com input/output reais**.

### 2.2 Premissas técnicas

- O compilador `simplesc` já existe e gera `.asm` válido para NASM 32-bit (ELF Linux), com syscalls `int 0x80`.
- **Desenvolvimento local**: qualquer host (x86_64 ou ARM64 macOS/Linux) com Docker + Docker Compose v2 — o sistema sobe inteiro com `docker compose up` em localhost.
- **Deploy de produção**: Oracle Cloud Infrastructure (OCI), instâncias **Ampere A1 (ARM64)** — Always Free tier permite até 4 OCPUs / 24 GB RAM gratuitos, suficientes pra v1.
- **Atenção arquitetural**: o compilador `simplesc` gera binários **x86 32-bit (ELF i386)** com syscalls `int 0x80`. Esses binários **não rodam nativamente em ARM64**. A solução adotada é emulação user-mode via **`qemu-user-static`** dentro do container sandbox — o overhead típico é 5-10x, mas como os programas SIMPLES são pequenos (escopo didático), o impacto na latência percebida é desprezível para a maioria dos exemplos. O timeout de execução foi calibrado considerando esse fator.
- Supabase (cloud, free tier inicial) é o provider de auth.
- **A linguagem SIMPLES tem `leia` (stdin)** — isso obriga o uso de WebSocket + PTY para execução interativa. REST e SSE não são suficientes.

---

## 3. Personas e user stories

### 3.1 Personas

| Persona | Perfil | Objetivo principal |
|---|---|---|
| **Aluno** (primário) | Estudante de Engenharia de Computação cursando a disciplina de Compiladores | Praticar SIMPLES sem instalar ambiente local |
| **Professor** (secundário) | Docente da disciplina de Compiladores | Demonstrar exemplos em sala/gravação e validar exercícios |

### 3.2 User stories (escopo v1)

- **US-01** — Como aluno, quero **fazer login** com minha conta institucional para acessar a IDE.
- **US-02** — Como aluno, quero **escrever código SIMPLES** com destaque das palavras reservadas, para identificar erros de digitação rapidamente.
- **US-03** — Como aluno, quero **clicar em Run** e ver o NASM gerado lado-a-lado, para entender a tradução.
- **US-04** — Como aluno, quero **executar o binário** e ver a saída no terminal, para validar a lógica.
- **US-05** — Como aluno, quero **digitar input via `leia`** no terminal, para programas que pedem dados.
- **US-06** — Como aluno, quero **expandir/contrair o painel NASM**, para focar só no editor quando for o caso.
- **US-07** — Como aluno, quero **interromper a execução** (botão Stop) caso meu programa entre em loop.
- **US-08** — Como aluno, quero **ver erros de compilação** com linha/coluna destacada no editor.
- **US-09** — Como aluno, quero **garantia de que loops infinitos não travam o serviço para outros**, para que minha experimentação não prejudique a turma (atendido por timeouts automáticos).
- **US-10** — Como professor, quero **isolamento por execução** garantindo que o código de um aluno não afete o ambiente de outros, para que demonstrações em sala sejam confiáveis.

### 3.3 User stories fora de escopo v1 (roadmap)

- US-F1 — Salvar histórico de código.
- US-F2 — Compartilhar snippet via URL.
- US-F3 — Estatísticas de uso por turma.
- US-F4 — Modo "passo-a-passo" (step debugger).

---

## 4. Escopo

### 4.1 Em escopo (v1)

- Editor SIMPLES com highlight das 27 palavras reservadas.
- Painel NASM gerado, sincronizado a cada compilação.
- Terminal interativo via WebSocket + PTY (suporta `leia`).
- Pipeline `simplesc → nasm → ld → execução em sandbox`.
- Autenticação Supabase (apenas gate de acesso).
- Timeouts em três camadas (compilação, execução wall-clock, hard limit Docker).
- Container Docker descartável por execução (segurança máxima).
- Stop/Cancel da execução em andamento.
- Mensagens de erro de compilação com linha/coluna.
- Deploy via Docker Compose + Nginx reverse proxy.

### 4.2 Fora de escopo (v1)

- Persistência de código (não há tabelas além do `auth.users` do Supabase).
- Compartilhamento público de snippets.
- Histórico de execuções por usuário.
- Step debugger / breakpoints.
- Suporte a múltiplos arquivos (`.simples` único por sessão).
- Integração com LMS (Moodle).
- Tema customizável (apenas dark padrão).

---

## 5. Requisitos funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF01 | O usuário deve autenticar via Supabase para acessar a IDE | Alta |
| RF02 | O editor deve aplicar syntax highlighting das 27 palavras reservadas SIMPLES | Alta |
| RF03 | O usuário deve poder escrever, editar e selecionar código no editor (atalhos padrão) | Alta |
| RF04 | Ao clicar em "Run", o frontend envia o código via WebSocket para o backend | Alta |
| RF05 | O backend invoca `simplesc` e retorna o NASM ou erros de compilação | Alta |
| RF06 | O painel NASM exibe o `.asm` gerado, com syntax highlighting de assembly | Alta |
| RF07 | O painel NASM pode ser expandido/contraído via splitter arrastável | Média |
| RF08 | Erros de compilação destacam a linha/coluna no editor SIMPLES | Alta |
| RF09 | Após compilação bem-sucedida, o backend monta (`nasm -f elf32`) e linka (`ld -m elf_i386`) | Alta |
| RF10 | O binário é executado em container Docker descartável | Alta |
| RF11 | A saída padrão (`escreva`/`escreval`) é transmitida em tempo real ao terminal frontend | Alta |
| RF12 | O usuário pode digitar no terminal — input vai para o stdin do binário (`leia`) | Alta |
| RF13 | O botão "Stop" envia SIGTERM ao processo, depois SIGKILL após 1s | Alta |
| RF14 | Execução é interrompida automaticamente após 10s wall-clock | Alta |
| RF15 | Compilação é interrompida após 15s | Alta |
| RF16 | O frontend exibe o exit code ao final da execução | Média |
| RF17 | O sistema rejeita código maior que 64 KB | Baixa |
| RF18 | O sistema aplica rate limiting de 30 execuções/minuto por usuário | Média |
| RF19 | Logout encerra a sessão e qualquer execução em andamento | Alta |
| RF20 | Health check endpoint `/api/health` retorna status dos componentes | Baixa |

---

## 6. Requisitos não-funcionais

### 6.1 Performance

- Latência de **WebSocket round-trip** (input no terminal → echo) ≤ 200 ms (p95) em rede regional.
- Tempo de **compilação + assembly + link** ≤ 2 s (p95) para programas até 200 LoC.
- Tempo de **spawn do container** de execução ≤ 300 ms (com pool pré-aquecido futuro; v1 aceita até 800 ms).
- **Throughput**: 50 execuções concorrentes por instância (escala horizontal via réplicas).

### 6.2 Segurança

- Sandbox por execução: container Docker descartável, `--network=none`, `--read-only`, cgroups.
- JWT do Supabase validado em **toda** conexão WebSocket e request REST.
- Rate limiting por user_id e por IP.
- Input validation: tamanho máximo de código (64 KB), caracteres não-imprimíveis bloqueados.
- Logs sem PII (apenas user_id hasheado).

### 6.3 Escalabilidade

- Backend stateless — múltiplas réplicas atrás do Nginx.
- Estado da sessão (PTY, container ID) mantido **em memória do worker** que aceitou o WebSocket. Sticky session via Nginx hash IP.
- Containers de execução criados sob demanda; v2 considera pool pré-aquecido.

### 6.4 Disponibilidade

- v1: SLA best-effort (deploy single-host).
- v2: alvo 99% (multi-host, health checks ativos, restart automático).

### 6.5 Observabilidade

- Logs estruturados em JSON (`structlog`), enviados ao stdout (capturados pelo Docker logging driver).
- Métricas básicas via Prometheus client (`/metrics` no backend).
- Distributed tracing fica para v2 (OpenTelemetry).

---

## 7. Arquitetura

### 7.1 Visão de componentes

```
┌──────────────────────────────────────────────────────────────────┐
│                          Cliente (Browser)                        │
│  React + TanStack Start + Tailwind                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │ Monaco      │  │ NASM viewer  │  │ xterm.js (terminal)  │     │
│  │ (SIMPLES)   │  │ (read-only)  │  │                      │     │
│  └─────────────┘  └──────────────┘  └──────────────────────┘     │
└─────────────┬──────────────────────────────┬─────────────────────┘
              │ HTTPS (auth, REST)           │ WSS (run, stdin/stdout)
              ▼                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Nginx (reverse proxy)                       │
│  TLS termination · WebSocket upgrade · sticky session             │
└─────────────┬──────────────────────────────┬─────────────────────┘
              │                              │
       ┌──────▼──────┐                ┌──────▼─────────────────┐
       │  Frontend   │                │  Backend               │
       │  (static)   │                │  Flask + flask-sock    │
       │  nginx:alp  │                │  asyncio + ptyprocess  │
       └─────────────┘                │  docker SDK            │
                                      │  + simplesc + nasm + ld│
                                      └──────┬─────────────────┘
                                             │ docker run --rm
                                             │ --network=none
                                             ▼
                                      ┌──────────────────────┐
                                      │ Sandbox container    │
                                      │ simples-runner:latest│
                                      │ (qemu-i386-static    │
                                      │  emula binário x86   │
                                      │  em hosts ARM64)     │
                                      └──────────────────────┘

External:  Supabase (Auth + Postgres) — apenas auth.users em v1
```

### 7.2 Componentes

| Componente | Responsabilidade |
|---|---|
| **Frontend** | UI da IDE, edição de código, render do NASM, terminal xterm.js, gerenciamento de sessão Supabase |
| **Nginx** | TLS, reverse proxy HTTP e WS, sticky session por IP hash |
| **Backend** | Auth verify, orquestrar pipeline de compilação, gerenciar PTY bridge, spawnar/destruir sandboxes |
| **Sandbox runner** | Imagem mínima que apenas executa o binário compilado, sem rede e com limites |
| **Supabase** | Auth (JWT, magic link/email-password), `auth.users` |

### 7.3 Fluxo de execução end-to-end

Quando o aluno clica em **Run**:

1. **Frontend**: serializa `{type: "compile_and_run", code: "<...>"}` e envia via WebSocket aberto e autenticado.
2. **Backend (worker)**: valida JWT (já validado no handshake; revalida tamanho do código).
3. **Backend**: cria diretório temporário `/tmp/sim-<uuid>/`, escreve `programa.simples`.
4. **Backend**: invoca `simplesc programa.simples -o programa.asm` com `subprocess.run(timeout=15)`.
   - Se erro: envia `{type: "compile_error", line, column, message}` e encerra.
   - Se sucesso: envia `{type: "asm_generated", asm: "<conteúdo>"}` para o painel NASM.
5. **Backend**: invoca `nasm -f elf32 programa.asm -o programa.o` (`timeout=15`).
6. **Backend**: invoca `ld -m elf_i386 programa.o -o programa` (`timeout=15`).
7. **Backend**: monta o sandbox via `docker SDK`:
   ```python
   container = docker_client.containers.run(
       image="simples-runner:latest",
       # qemu-i386-static emula o binário x86 — funciona tanto em hosts x86_64 quanto ARM64
       command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
       volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
       network_mode="none",
       mem_limit="128m",
       cpu_quota=50000,           # 50% de 1 CPU
       pids_limit=64,
       read_only=True,
       tmpfs={"/tmp": "size=8m"},
       user="65534:65534",        # nobody
       detach=True,
       stdin_open=True,
       tty=True,
       remove=False,              # destruímos manualmente após bridge fechar
   )
   ```
8. **Backend**: anexa-se ao container via `container.attach_socket(params={...stdin/stdout/stderr/stream...})`. Esse socket vira o equivalente ao "PTY master" do nosso bridge.
9. **Backend**: roda duas tasks `asyncio` em paralelo:
   - `pty_to_ws`: lê do socket do container, emite `{type: "stdout", data: ...}` no WebSocket.
   - `ws_to_pty`: recebe `{type: "stdin", data: ...}` do WebSocket, escreve no socket.
10. **Backend**: arma `asyncio.wait_for(execution_task, timeout=10)`.
    - Se completa: envia `{type: "exit", code: <exit_code>}`.
    - Se TimeoutError: container.kill(SIGTERM) → 1s → container.kill(SIGKILL); envia `{type: "timeout"}`.
11. **Backend**: `container.remove(force=True)` e limpa `tmpdir`.
12. **Frontend**: xterm.js renderiza cada chunk; o estado da UI volta para "idle" e o botão Run reaparece.

> **Analogia (Strategy Pattern):** o passo 7-11 é um `PtyExecutionStrategy.execute()`. Se amanhã quisermos suportar batch execution (sem stdin), basta plugar uma `CapturedExecutionStrategy` que usa `subprocess.run(stdin=PIPE)` — o resto do pipeline não muda.

### 7.4 Padrões de projeto aplicados

| Padrão | Onde | Por quê |
|---|---|---|
| **Strategy** | `ExecutionStrategy` (PTY vs Captured) | Permite trocar como a saída chega ao usuário sem mexer no pipeline de compilação |
| **Façade** | `CompilerService.compile_and_run(code)` | Esconde a orquestração `simplesc → nasm → ld → docker run` atrás de uma única interface |
| **Factory** | `SandboxFactory.create(binary_path)` | Centraliza a criação de containers com limites consistentes |
| **Repository** (futuro) | `CodeSnippetRepository` (v2) | Quando salvarmos código, isolar acesso a Supabase do resto da aplicação |
| **Observer** | Eventos WebSocket (`compile_started`, `asm_generated`, `stdout`, etc.) | Frontend reage a eventos discretos sem polling |
| **Command** | Mensagens de cliente (`{type: "compile_and_run"}`, `{type: "stdin"}`, `{type: "stop"}`) | Cada mensagem é um comando autocontido |

---

## 8. Stack técnica

### 8.1 Frontend

| Item | Versão / fonte | Observação |
|---|---|---|
| **React** | 18.x | Base UI |
| **TypeScript** | 5.x | Tipagem |
| **TanStack Start** | latest | Framework full-stack baseado em React + TanStack Router |
| **TanStack Query** | 5.x | Gerenciamento de estado de requisições REST |
| **TanStack Router** | 1.x | Routing tipado |
| **Tailwind CSS** | 3.x | Utility-first styling |
| **Monaco Editor** | `@monaco-editor/react` | Editor (mesmo do VS Code) |
| **xterm.js** | 5.x | Emulador de terminal |
| `xterm-addon-fit` | latest | Resize do terminal |
| **@supabase/supabase-js** | 2.x | Auth client |
| **@supabase/auth-ui-react** | latest | UI de login pronta (rapidez de v1) |
| `react-resizable-panels` | latest | Splitter para painéis NASM e Terminal |

### 8.2 Backend

| Item | Versão | Observação |
|---|---|---|
| **Python** | 3.11+ | |
| **Flask** | 3.x | API REST |
| **flask-sock** | latest | WebSocket sobre Flask (simples, sem Socket.IO) |
| **asyncio** + `gevent` | stdlib + 23.x | Concorrência. `flask-sock` usa gevent por padrão |
| **docker SDK** | 7.x | Spawn de containers de execução |
| **PyJWT** | 2.x | Validação de JWT do Supabase |
| **structlog** | 24.x | Logs estruturados |
| **prometheus-client** | latest | Métricas em `/metrics` |
| **pytest** | 8.x | Testes |

### 8.3 Compilador (já existente)

- `simplesc` — binário em C99, gera `.asm` para NASM 32-bit.
- **NASM** 2.15+ (`apt install nasm`) — cross-assembler, roda em qualquer host CPU.
- **binutils-i686-linux-gnu** — provê `i686-linux-gnu-ld` para linkar ELF i386 em qualquer host (x86_64 ou ARM64).
- **qemu-user-static** — emula execução x86 32-bit em hosts ARM64 (incluído no container `runner`).

### 8.4 Infraestrutura

- **Docker** 24.x + **Docker Compose** v2.
- **Nginx** 1.25+ — reverse proxy + TLS.
- **Supabase** — cloud (free tier). Self-hosted é opção para v2.

---

## 9. API design — REST + WebSocket

### 9.1 REST endpoints

Todos os endpoints exigem `Authorization: Bearer <jwt>` (JWT do Supabase), exceto `/api/health`.

| Método | Path | Descrição | Resposta |
|---|---|---|---|
| `GET` | `/api/health` | Health check público | `{status, version, components: {compiler, docker, supabase}}` |
| `POST` | `/api/auth/verify` | Valida JWT (chamado opcionalmente pelo frontend após login) | `{valid: true, user_id, email}` |
| `GET` | `/api/limits` | Limites atuais (timeout, max_code_size, rate_limit) | `{exec_timeout_s: 10, compile_timeout_s: 15, max_code_kb: 64, runs_per_minute: 30}` |
| `GET` | `/metrics` | Prometheus metrics (network: interno apenas) | `text/plain` |

### 9.2 WebSocket — `/ws/run`

**Handshake**: o frontend envia `Sec-WebSocket-Protocol: bearer.<jwt>` (ou query param `?token=<jwt>` se o navegador não permitir customizar protocols facilmente). O backend valida o JWT antes de aceitar o upgrade.

**Formato das mensagens**: JSON, uma mensagem por frame.

#### 9.2.1 Mensagens cliente → servidor

```jsonc
// Iniciar compilação e execução
{ "type": "compile_and_run", "code": "programa teste\n  inteiro x\ninicio\n  leia x\n  escreva x\nfim\n" }

// Enviar input para o stdin do binário em execução
{ "type": "stdin", "data": "42\n" }

// Cancelar execução em andamento
{ "type": "stop" }

// Keepalive (opcional, frontend envia a cada 30s)
{ "type": "ping" }
```

#### 9.2.2 Mensagens servidor → cliente

```jsonc
{ "type": "compile_started" }

// Erro na fase de compilação SIMPLES
{ "type": "compile_error", "phase": "lexer|parser|semantic", "line": 4, "column": 7, "message": "variavel 'y' nao declarada" }

// NASM gerado com sucesso — frontend popula o painel direito
{ "type": "asm_generated", "asm": "section .bss\n    x resd 1\n..." }

// Erros de fases pós-compilação
{ "type": "assemble_error", "stderr": "..." }
{ "type": "link_error",     "stderr": "..." }

// Execução começou — frontend habilita o terminal e o botão Stop
{ "type": "exec_started" }

// Output em tempo real
{ "type": "stdout", "data": "Digite um numero: " }
{ "type": "stderr", "data": "..." }

// Execução terminou
{ "type": "exit", "code": 0, "duration_ms": 1234 }

// Timeout
{ "type": "timeout", "limit_s": 10 }

// Erro inesperado (sandbox falhou subir, etc.)
{ "type": "internal_error", "message": "..." }

{ "type": "pong" }
```

#### 9.2.3 Máquina de estados do servidor (por conexão)

```
IDLE
  └─ recv compile_and_run ─▶ COMPILING
COMPILING
  ├─ erro              ─▶ envia compile_error  ─▶ IDLE
  └─ ok (asm + link)   ─▶ envia asm_generated  ─▶ EXECUTING
EXECUTING
  ├─ stdout/stderr     ─▶ envia stdout/stderr (loop)
  ├─ recv stdin        ─▶ escreve no PTY (loop)
  ├─ recv stop         ─▶ kill ─▶ envia exit(SIGKILL)  ─▶ IDLE
  ├─ exit normal       ─▶ envia exit                    ─▶ IDLE
  └─ wall-clock 10s    ─▶ kill ─▶ envia timeout         ─▶ IDLE
```

Mensagens recebidas em estado inválido (ex.: `stdin` durante `IDLE`) são descartadas com log de warning — não derrubam a conexão.

---

## 10. Modelo de dados (Supabase)

### 10.1 v1 — apenas auth

A v1 usa **somente** a tabela `auth.users` que o Supabase já fornece nativamente. O backend valida o JWT e extrai `user_id` (`sub` do JWT) sem consultar o banco.

```
auth.users (gerenciada pelo Supabase)
  ├─ id           uuid (PK)
  ├─ email        text
  ├─ created_at   timestamptz
  └─ ...
```

### 10.2 (Futuro v2) — schema previsto

Quando entrarmos no escopo de salvar histórico/snippets, o schema será:

```sql
create table public.code_snippets (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  title        text not null,
  code         text not null,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

create table public.executions (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id) on delete cascade,
  snippet_id      uuid references public.code_snippets(id) on delete set null,
  status          text not null check (status in ('compile_error','runtime_error','timeout','success')),
  duration_ms     integer,
  exit_code       integer,
  created_at      timestamptz default now()
);

-- RLS (Row-Level Security)
alter table public.code_snippets enable row level security;
create policy "users see only their snippets"
  on public.code_snippets for all
  using (auth.uid() = user_id);

alter table public.executions enable row level security;
create policy "users see only their executions"
  on public.executions for all
  using (auth.uid() = user_id);
```

> Padrão **Repository** será aplicado aqui: `SnippetRepository` e `ExecutionRepository` isolam `supabase-py` do resto do código.

---

## 11. Segurança e sandboxing

### 11.1 Autenticação e autorização

- Usuário autentica via Supabase no frontend (email + senha em v1, magic link opcional).
- Frontend recebe JWT (`access_token`) e o envia em **toda** request REST e no handshake do WebSocket.
- Backend valida o JWT usando o `JWT_SECRET` do Supabase (não consulta banco — performance).
- `user_id` extraído de `sub` do JWT é o identificador canônico para rate limiting e logs.

### 11.2 Sandboxing por execução

Camadas de defesa do mais externo ao mais interno:

| Camada | Mecanismo | Configuração |
|---|---|---|
| 1. Container descartável | `docker run --rm` por execução | Container destruído após exec |
| 2. Network isolation | `--network=none` | Sem qualquer rede |
| 3. Filesystem | `--read-only` + `tmpfs:/tmp,size=8m` | FS imutável, /tmp em RAM limitado |
| 4. Memória | `--memory=128m --memory-swap=128m` | Sem swap, OOM kill rápido |
| 5. CPU | `--cpus=0.5` (cgroups) | Meia CPU |
| 6. PIDs | `--pids-limit=64` | Bloqueia fork bomb |
| 7. Usuário | `--user=65534:65534` (nobody) | Não-root dentro do container |
| 8. Capabilities | `--cap-drop=ALL` | Sem capabilities Linux |
| 9. Seccomp | profile padrão do Docker | Bloqueia syscalls perigosas |

### 11.3 Timeouts em três camadas (defense in depth)

```
[1] Compile timeout      subprocess.run(timeout=15)        — para simplesc, nasm, ld separadamente
[2] Wall-clock timeout   asyncio.wait_for(exec, timeout=10) — soft, manda SIGTERM, depois SIGKILL
[3] Hard limit Docker    --stop-timeout=12                  — rede de segurança caso [2] falhe
```

### 11.4 Rate limiting

- **30 execuções/minuto** por `user_id`.
- **120 execuções/minuto** por IP (proteção adicional contra abuso após token roubado).
- Implementação: `flask-limiter` com backend Redis (em v1, in-memory é aceitável).

### 11.5 Input validation

- `code` ≤ 64 KB (rejeita acima).
- `code` deve ser UTF-8 válido e conter apenas caracteres `\t \n \r` + printáveis ASCII/extended.
- `stdin.data` por mensagem ≤ 4 KB.

### 11.6 Threat model resumido

| Ameaça | Mitigação |
|---|---|
| Loop infinito | Wall-clock timeout (10s) |
| Fork bomb | `--pids-limit=64` |
| Memória ilimitada | `--memory=128m` |
| Exfiltração via rede | `--network=none` |
| Escape do container | Não-root + `--cap-drop=ALL` + seccomp |
| Abuso de execuções | Rate limit por user e IP |
| JWT roubado | Expiração curta (1h padrão Supabase) + RLS futuro |
| Code injection no shell | Backend usa `subprocess` com lista de args, nunca `shell=True` |

---

## 12. UI/UX

### 12.1 Layout (desktop ≥ 1280px)

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER: logo "Simples Editor"           [user@email]  [Sair]    │
├──────────────────────────────────────────────────────────────────┤
│  TOOLBAR: [▶ Run]  [■ Stop]  [Limpar]      [exemplos ▾]         │
├────────────────────────────┬─────────────────────────────────────┤
│                            │ ║ NASM x32                          │
│  EDITOR (Monaco)           │ ║ (read-only)                       │
│  programa exemplo          │ ║ section .bss                      │
│    inteiro x               │ ║     x resd 1                      │
│  inicio                    │ ║                                   │
│    leia x                  │ ║ section .text                     │
│    escreva x               │ ║     global _start                 │
│  fim                       │ ║ _start:                           │
│                            │ ║     mov eax, 3                    │
│                            │ ║     ...                           │
│                            │ ║                                   │
├────────────────────────────┴─────────────────────────────────────┤
│  TERMINAL (xterm.js)                       [⌃C interrompe]      │
│  Digite um numero: 42                                             │
│  42                                                               │
│  [exit code: 0 — 0.18s]                                           │
└──────────────────────────────────────────────────────────────────┘
```

- **Splitter vertical** entre Editor e NASM (arrastável; double-click colapsa o painel NASM para 0%, segundo double-click restaura).
- **Splitter horizontal** entre área superior e Terminal (arrastável; mínimo 100px no terminal).
- **Mobile (< 1024px)**: layout em abas (Editor / NASM / Terminal). MVP suporta apenas desktop; mobile fica para v1.1.

### 12.2 Comportamentos chave

- Ao **clicar Run**:
  - Editor entra em modo read-only.
  - Painel NASM mostra placeholder "compilando..." → preenche assim que `asm_generated` chega.
  - Terminal limpa e mostra cursor piscando.
  - Botão Run vira "Stop".
- Ao **clicar Stop**: envia `{type: "stop"}` ao servidor; UI volta a estado idle ao receber `exit`.
- **Erro de compilação**: linha destacada em vermelho no editor (Monaco markers); painel NASM mostra a mensagem; terminal não é tocado.
- **Botão "exemplos"**: dropdown com `hello`, `fatorial`, `fibonacci`, `tabuada` — carrega no editor.

### 12.3 Estados visuais

| Estado | Editor | NASM | Terminal | Run/Stop |
|---|---|---|---|---|
| `idle` | editável | mensagem inicial | vazio | Run habilitado |
| `compiling` | read-only | spinner | limpo | Stop |
| `compile_error` | linha em vermelho | mensagem de erro | limpo | Run habilitado |
| `executing` | read-only | NASM exibido | recebendo output | Stop |
| `finished` | editável | NASM exibido | output + exit code | Run habilitado |

---

## 13. Editor de código (Monaco)

### 13.1 Linguagem custom "simples"

Registramos uma linguagem custom no Monaco com `monaco.languages.register({ id: "simples" })` e definimos:

#### Palavras reservadas (27)

```ts
const SIMPLES_KEYWORDS = [
  // Estrutura
  "programa", "inicio", "fim",
  // Tipos
  "inteiro", "flutuante", "vazio",
  // Controle
  "se", "entao", "senao", "fimse",
  // Laços
  "enquanto", "fimenquanto",
  "para", "de", "ate", "passo", "faca", "fimpara",
  // E/S
  "leia", "escreva", "escreval",
  // Lógicos
  "e", "ou", "nao",
  // Operador
  "div",
  // Subprograma (out of scope v1, mas highlight desde já)
  "procedimento", "retorna",
] as const;
```

#### Tokenizer Monarch (resumo)

```ts
monaco.languages.setMonarchTokensProvider("simples", {
  ignoreCase: true,
  keywords: SIMPLES_KEYWORDS,
  operators: ["<-", "+", "-", "*", "div", ">", "<", "=", "<>", ">=", "<="],
  symbols: /[=<>+\-*]+/,
  tokenizer: {
    root: [
      [/[a-zA-Z_]\w*/, {
        cases: { "@keywords": "keyword", "@default": "identifier" }
      }],
      [/\d+\.\d+/, "number.float"],
      [/\d+/, "number"],
      [/<-/, "operator"],
      [/@symbols/, { cases: { "@operators": "operator", "@default": "" } }],
      [/[(),;]/, "delimiter"],
      [/\s+/, "white"],
    ],
  },
});
```

#### Tema

Tema dark customizado, com keywords em ciano, números em laranja, identificadores neutros, comentários (futuro) em verde.

### 13.2 Erros de compilação como markers

Quando o backend envia `compile_error`, o frontend converte em Monaco marker:

```ts
monaco.editor.setModelMarkers(model, "simplesc", [{
  severity: monaco.MarkerSeverity.Error,
  startLineNumber: err.line,
  endLineNumber: err.line,
  startColumn: err.column,
  endColumn: err.column + 1,
  message: err.message,
}]);
```

### 13.3 Snippets

Snippets básicos pra acelerar (v1):

- `prog` → `programa <nome>\n  \ninicio\n  \nfim`
- `enq`  → `enquanto <cond> faca\n  \nfimenquanto`
- `se`   → `se <cond> entao\n  \nfimse`
- `para` → `para <i> de <a> ate <b> passo <p> faca\n  \nfimpara`

---

## 14. Docker Compose

### 14.1 Topologia

```
docker-compose.yml define 4 serviços:
  - frontend  (estático, servido pelo nginx_app)
  - backend   (Flask + simplesc + nasm + ld; precisa de Docker socket pra spawnar runner)
  - nginx_app (reverse proxy)
  - runner_image (build only — não roda como serviço; é a imagem usada pra spawn)

Externos:
  - Supabase (cloud)
```

### 14.2 `docker-compose.yml` (exemplo de referência)

```yaml
version: "3.9"

services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    expose:
      - "80"
    environment:
      - VITE_SUPABASE_URL=${SUPABASE_URL}
      - VITE_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - VITE_API_BASE=/api
      - VITE_WS_BASE=/ws
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    expose:
      - "5000"
    environment:
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
      - EXEC_TIMEOUT_S=10
      - COMPILE_TIMEOUT_S=15
      - MAX_CODE_KB=64
      - RUNS_PER_MINUTE=30
      - SANDBOX_IMAGE=simples-runner:latest
      - LOG_LEVEL=INFO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock   # spawn de containers
      - simples_tmp:/tmp/simples
    depends_on:
      - runner_image_build
    restart: unless-stopped

  # Pseudo-serviço apenas para construir a imagem do sandbox
  runner_image_build:
    image: simples-runner:latest
    build:
      context: ./runner
      dockerfile: Dockerfile
    command: ["true"]      # sai imediatamente; só queremos a imagem construída
    restart: "no"

volumes:
  simples_tmp:
```

### 14.3 `backend/Dockerfile`

A imagem do backend precisa de **toolchain cross-target i386** para que `nasm` e `ld` produzam binários x86 32-bit independentemente da arquitetura do host (x86_64 em desenvolvimento local, ARM64 na Oracle Cloud Ampere A1). Usamos `binutils-i686-linux-gnu`, que provê `i686-linux-gnu-ld` funcionando idêntico em ambas arquiteturas — abordagem mais portável que `gcc-multilib`, que só existe em x86_64.

```dockerfile
# Funciona em x86_64 (dev local) e ARM64 (Oracle Cloud Ampere A1)
FROM ubuntu:24.04

# Toolchain cross-target i386 + Python
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      nasm \
      binutils-i686-linux-gnu \
      python3.11 python3.11-venv python3-pip \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Compilador SIMPLES (já existente, compilamos dentro da imagem com gcc nativo do host)
COPY ./simples-compiler /opt/simples-compiler
RUN cd /opt/simples-compiler && make && cp simplesc /usr/local/bin/simplesc

# Backend Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", \
     "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

> **Nota de invocação no código Python**: ao linkar, use `subprocess.run(["i686-linux-gnu-ld", "-m", "elf_i386", ...])` em vez de `["ld", "-m", "elf_i386", ...]`. O `nasm -f elf32` continua sendo invocado como `["nasm", "-f", "elf32", ...]` — NASM é nativamente cross-assembler e funciona em qualquer host CPU.

### 14.4 `runner/Dockerfile` (sandbox de execução)

Imagem mínima — só precisa rodar o binário ELF 32-bit, **independentemente da arquitetura do host**. Como o NASM gerado pelo `simplesc` usa `int 0x80` direto (sem chamar libc), não é preciso `libc6:i386` no sandbox; basta o `qemu-user-static`, que emula a CPU x86 e dispatcha os syscalls.

```dockerfile
FROM debian:12-slim

# qemu-user-static permite executar binários x86 32-bit em hosts x86_64 e ARM64
# (em x86_64 a emulação é redundante, mas o overhead é desprezível e mantém
#  uma única imagem de runner para os dois alvos)
RUN apt-get update && apt-get install -y --no-install-recommends \
      qemu-user-static \
    && rm -rf /var/lib/apt/lists/*

# Usuário não-root para execução
RUN useradd -u 65534 -M -s /usr/sbin/nologin sandbox || true

USER 65534:65534
WORKDIR /sandbox
```

> **Como é invocado**: o backend roda `docker run ... simples-runner:latest /usr/bin/qemu-i386-static /sandbox/programa`. Em ambientes x86_64 puros (sem ARM no horizonte), poderíamos opcionalmente invocar direto `/sandbox/programa` se `binfmt_misc` estiver registrado no host — mas usar `qemu-i386-static` explicitamente é mais portável e elimina dependência de configuração do host.

### 14.5 `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-static.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 14.6 Deployment local (desenvolvimento)

Funciona em **qualquer host com Docker** — Linux x86_64, macOS Apple Silicon (ARM), macOS Intel, ou Windows com WSL2. Como o `runner` usa `qemu-user-static`, a emulação x86 funciona uniformemente em todas essas arquiteturas.

**Pré-requisitos do host de desenvolvimento**:

- Docker Engine 24+ ou Docker Desktop
- Docker Compose v2
- Conta no Supabase (free tier) com projeto criado e `JWT_SECRET` em mãos

**Passo a passo**:

```bash
# 1. Clonar o repositório (com submodules para o simples-compiler)
git clone --recurse-submodules https://github.com/<org>/simples-online.git
cd simples-online

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET

# 3. Subir todos os serviços
docker compose up --build -d

# 4. Acessar
# Frontend:  http://localhost
# Backend health:  http://localhost/api/health
# Logs em tempo real:  docker compose logs -f
```

Em desenvolvimento, o Nginx local serve em HTTP puro (porta 80) — TLS fica para o deploy de produção. As variáveis `VITE_API_BASE` e `VITE_WS_BASE` apontam para `/api` e `/ws` (caminhos relativos), então o frontend funciona em `localhost`, IP de LAN, túnel `ngrok` ou domínio de staging sem alteração de código.

### 14.7 Deployment Oracle Cloud Infrastructure (Ampere A1, ARM64)

Deploy alvo de produção: **OCI Ampere A1 (Always Free)** com Ubuntu 22.04 LTS aarch64. Free tier permanente: 4 OCPUs / 24 GB RAM / 200 GB block storage / 10 TB egress mensal.

#### 14.7.1 Provisionamento da VM

Via console OCI (caminho mais rápido para v1):

1. **Compute → Instances → Create Instance**.
2. **Image**: `Canonical Ubuntu 22.04 (aarch64)`.
3. **Shape**: `VM.Standard.A1.Flex` — configurar 2 OCPUs e 12 GB RAM (suficiente para v1; sobra para staging ou outra carga futura).
4. **Networking**: criar/usar VCN com subnet pública, atribuir IP público (efêmero ou reservado).
5. **SSH keys**: subir chave pública pré-gerada localmente.
6. **Boot volume**: 50 GB padrão.

> Para reproducibilidade e versionamento, ver Apêndice F (Terraform completo). O console é caminho rápido para o primeiro deploy; Terraform é o caminho oficial para criar/recriar o ambiente.

#### 14.7.2 Configuração da Security List (firewall a nível de subnet)

Adicionar **Ingress Rules** na security list da subnet:

| Source | Protocol | Port | Descrição |
|---|---|---|---|
| `0.0.0.0/0` | TCP | 80 | HTTP — redirect para HTTPS via nginx |
| `0.0.0.0/0` | TCP | 443 | HTTPS |
| `<seu-ip>/32` | TCP | 22 | SSH (restrito ao seu IP, não 0.0.0.0/0) |

> **Atenção crítica**: o Ubuntu na OCI vem com `iptables` bloqueando portas além de 22 por padrão. Além da Security List, é obrigatório liberar no firewall do host:
>
> ```bash
> sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
> sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
> sudo netfilter-persistent save
> ```
>
> Esquecer este passo é o erro #1 que faz parecer "a VM tá fora do ar" quando na verdade só o `iptables` local está rejeitando.

#### 14.7.3 Bootstrap do host (Ubuntu 22.04)

```bash
# SSH na VM
ssh ubuntu@<ip-público>

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Docker Engine + Compose v2 (repositório oficial — versão ARM64)
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin

# Permitir uso sem sudo
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
docker run --rm hello-world

# (Opcional) registrar binfmt_misc no host para executar binários x86
# transparentemente — não é necessário se o backend invoca qemu-i386-static
# explicitamente, mas habilita docker run --platform=linux/386 ...
docker run --privileged --rm tonistiigi/binfmt --install i386
```

#### 14.7.4 Deploy da aplicação

```bash
# Clonar e configurar
git clone --recurse-submodules https://github.com/<org>/simples-online.git
cd simples-online
cp .env.example .env
nano .env   # preencher SUPABASE_*, ajustar EXEC_TIMEOUT_S=15 se necessário

# Build e subir
docker compose up --build -d

# Confirmar
docker compose ps
curl -k https://localhost/api/health
```

#### 14.7.5 TLS via Let's Encrypt

Apontar um subdomínio (ex.: `simples.seu-dominio.edu.br`) para o IP público OCI. Em seguida:

```bash
# Instalar certbot via snap (ARM64 suportado)
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Parar nginx temporariamente para liberar porta 80
docker compose stop nginx

# Emitir certificado em modo standalone
sudo certbot certonly --standalone -d simples.seu-dominio.edu.br \
     --non-interactive --agree-tos -m admin@seu-dominio.edu.br

# Copiar certificados para o volume do nginx
sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/fullchain.pem ./nginx/certs/
sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/privkey.pem ./nginx/certs/

# Subir nginx novamente
docker compose start nginx

# Renovação automática (via cron)
echo "0 3 * * * certbot renew --quiet --post-hook 'cd /home/ubuntu/simples-online && docker compose restart nginx'" | sudo crontab -
```

#### 14.7.6 Considerações específicas de ARM64

| Aspecto | Observação |
|---|---|
| **Imagens base** | Todas as imagens usadas (`ubuntu:24.04`, `debian:12-slim`, `nginx:1.25-alpine`, `node:20-alpine`) têm builds multi-arch oficiais. O Docker baixa automaticamente a variante ARM64 no host. |
| **Build do simples-compiler** | Acontece dentro do container backend com `gcc` nativo do Ubuntu — produz `simplesc` ARM64 que invoca `nasm`/`ld` para gerar binários x86 (saída cross-target). |
| **Overhead do qemu-user** | 5-10x para programas compute-bound. Para programas SIMPLES típicos (fatorial até 12, fibonacci até 20), latência adicional fica em < 50ms — imperceptível. Recomendado aumentar `EXEC_TIMEOUT_S` de 10 para 15 em produção ARM. |
| **Dimensionamento da VM** | 2 OCPU + 12 GB RAM atendem ~50 alunos concorrentes (cada execução consome 128 MB cap; sobra folga). Se precisar mais headroom, escalar para 4 OCPU + 24 GB (limite Free Tier) sem custo. |
| **Rede** | OCI cobra apenas saída acima de 10 TB/mês — para uso acadêmico, jamais será atingido. Tráfego entre serviços do compose é localhost, não conta. |

---

## 15. Nginx — reverse proxy

### 15.1 `nginx/nginx.conf` (essencial)

```nginx
worker_processes auto;
events { worker_connections 1024; }

http {
  include       mime.types;
  default_type  application/octet-stream;
  sendfile      on;
  keepalive_timeout 65;

  # WebSocket upgrade
  map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
  }

  upstream frontend_upstream { server frontend:80; }
  upstream backend_upstream  { server backend:5000;  }

  server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
  }

  server {
    listen 443 ssl http2;
    server_name simples.example.edu.br;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Frontend (estático)
    location / {
      proxy_pass http://frontend_upstream;
      proxy_set_header Host $host;
    }

    # API REST
    location /api/ {
      proxy_pass http://backend_upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_read_timeout 30s;
    }

    # WebSocket
    location /ws/ {
      proxy_pass http://backend_upstream;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_read_timeout 600s;     # > exec_timeout
      proxy_send_timeout 600s;
    }

    # Bloqueia /metrics externamente
    location = /metrics { deny all; return 403; }

    client_max_body_size 256k;     # > max_code_kb com folga
  }
}
```

> **Sticky session via IP hash** entra em v2 quando tivermos múltiplas réplicas do backend. Em v1 (single backend) é desnecessário.

---

## 16. Observabilidade

### 16.1 Logs estruturados (JSON)

Cada log line do backend é um JSON com campos fixos:

```json
{
  "timestamp": "2026-05-05T20:31:12.345Z",
  "level": "INFO",
  "logger": "simples.executor",
  "event": "execution_finished",
  "user_id": "uuid-...",
  "duration_ms": 234,
  "exit_code": 0,
  "request_id": "req-..."
}
```

### 16.2 Métricas Prometheus (`/metrics`)

| Métrica | Tipo | Labels |
|---|---|---|
| `simples_compile_duration_seconds` | histogram | `phase=lexer\|parser\|nasm\|ld` |
| `simples_execution_duration_seconds` | histogram | `outcome=success\|timeout\|runtime_error` |
| `simples_executions_total` | counter | `outcome` |
| `simples_active_sandboxes` | gauge | — |
| `simples_compile_errors_total` | counter | `phase` |
| `simples_websocket_connections` | gauge | — |

### 16.3 Health check

`GET /api/health` retorna:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "compiler": {"status": "ok", "version": "simplesc 1.0"},
    "nasm":     {"status": "ok", "version": "2.16"},
    "docker":   {"status": "ok"},
    "supabase": {"status": "ok"}
  }
}
```

---

## 17. Estratégia de testes

### 17.1 Backend (pytest)

- **Unit**: cada estratégia (`PtyExecutionStrategy`, `CapturedExecutionStrategy`), cada validador.
- **Integration**: pipeline `simplesc → nasm → ld` com fixtures de programas SIMPLES.
- **E2E (backend-only)**: cliente WebSocket de teste roda os 7 exemplos do PRD do compilador (atribuição, leia/escreva, se, enquanto, para, fatorial, fibonacci) e verifica saída esperada.

### 17.2 Frontend (Vitest + React Testing Library)

- Componente do editor — renderiza, aceita digitação, marca erros.
- Componente do terminal — recebe stdout, envia stdin.
- Hook de WebSocket — reconecta, transiciona estados corretamente.

### 17.3 E2E (Playwright — v1.1)

- Login → editar exemplo → Run → ver output esperado.
- Stop interrompe.
- Timeout encerra após 10s.

### 17.4 Compilador SIMPLES

Já testado com Unity (TDD existente, ver [PRD do compilador](https://www.notion.so/344a6259575b81098b28f3235354d86b)). Não é refeito aqui.

---

## 18. Roadmap

### Fase 1 — MVP (4 semanas)

| Semana | Entregáveis |
|---|---|
| 1 | Skeleton frontend (TanStack Start), backend Flask, auth Supabase, deploy Docker Compose básico |
| 2 | Editor Monaco com SIMPLES highlighting, painel NASM read-only, REST `/api/health` |
| 3 | WebSocket `/ws/run`, pipeline `simplesc → nasm → ld`, sandbox Docker, terminal xterm.js funcional |
| 4 | Stop, timeouts, rate limit, erros com markers, polishing UI, testes |

### Fase 2 — Estabilização (2 semanas)

- Logs estruturados + métricas Prometheus.
- Documentação para alunos.
- Testes E2E (Playwright).
- Deploy em staging na **Oracle Cloud Ampere A1** (Ubuntu 22.04 ARM64) — validação de qemu-user + cross-toolchain em ambiente real.
- Coleta de feedback piloto (1 turma).

### Fase 3 — Recursos (futuro)

- Salvar histórico de código (Repository + RLS).
- Compartilhar snippet via URL.
- Pool de sandboxes pré-aquecido (latência < 100ms).
- Modo "passo-a-passo" (debugger).
- Mobile responsivo (abas).
- Integração Moodle (LTI).

---

## 19. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aluno consegue escapar do sandbox | Baixa | Crítico | `--cap-drop=ALL` + non-root + `--network=none` + seccomp + `--read-only`. Auditoria periódica das opções Docker. |
| Backend cai sob carga | Média | Alto | Rate limit + queue de execução + alarme em `simples_active_sandboxes` > N |
| Spawn de container lento (> 1s) | Média | Médio | v2: pool pré-aquecido. v1: comunicar latência ao usuário ("preparando ambiente...") |
| **Overhead de emulação x86 em ARM (qemu-user)** | **Alta** | **Baixo** | **Esperado para todos os hosts ARM. Calibrar `EXEC_TIMEOUT_S=15` em produção. Programas didáticos típicos têm latência adicional < 50ms — imperceptível.** |
| Bug no compilador `simplesc` | Média | Médio | Já tem TDD — capturar stderr e mostrar como `compile_error` em vez de derrubar a sessão |
| JWT do Supabase expira mid-execution | Alta | Baixo | WebSocket aceita reconexão; refresh token automático no client |
| Custos cloud (OCI/Supabase) | Baixa | Baixo | OCI Ampere A1 é Always Free permanente (4 OCPU/24GB). Supabase free tier suporta o piloto. Alarmes de billing como rede de segurança. |
| Aluno digita código gigante (DoS) | Média | Baixo | Limite de 64 KB no frontend e validação no backend |
| Container não é destruído (leak) | Baixa | Alto | `docker run --rm` + cron de limpeza diário (`docker container prune --filter ...`) |
| **Conta OCI suspensa por inatividade (Free Tier)** | **Média** | **Médio** | **Habilitar Pay-As-You-Go (não cobra automaticamente, mas evita suspensão). Acessar console mensalmente.** |
| **iptables do Ubuntu 22.04 OCI bloqueando 80/443** | **Alta** | **Médio** | **Documentado no playbook (§14.7.2). Adicionado ao checklist de bootstrap.** |

---

## 20. Critérios de aceite

- [ ] Aluno autenticado consegue abrir a IDE e ver o editor.
- [ ] Os 7 exemplos canônicos (atribuição, leia/escreva, se, enquanto, para, expressões, fatorial) compilam, exibem NASM e executam corretamente.
- [ ] `leia` no terminal aceita input do usuário e o programa prossegue.
- [ ] Erro de compilação destaca a linha correta no editor.
- [ ] Loop infinito (`enquanto 1 = 1 faca ... fimenquanto`) é interrompido em ≤ 11s e mostra `timeout`.
- [ ] Botão Stop interrompe execução em andamento em ≤ 2s.
- [ ] Painel NASM expande/contrai via splitter.
- [ ] Logout encerra qualquer execução ativa do usuário.
- [ ] `docker compose up` levanta o sistema completo num host limpo de desenvolvimento (Linux x86_64 ou macOS ARM com Docker instalado).
- [ ] Deploy em Oracle Cloud Ampere A1 (Ubuntu 22.04 ARM64) funciona end-to-end via os passos de §14.7.
- [ ] `make test` no backend passa com 0 falhas.
- [ ] Métricas Prometheus expostas em `/metrics` (interno).

---

## 21. Apêndices

### A. Exemplo completo: programa fatorial

**Editor (SIMPLES):**
```
programa fatorial
  inteiro n, fat, contador
inicio
  leia n
  fat <- 1
  contador <- 1
  enquanto contador < n faca
    contador <- contador + 1
    fat <- fat * contador
  fimenquanto
  escreva fat
fim
```

**Painel NASM (gerado):**
```nasm
section .bss
    n        resd 1
    fat      resd 1
    contador resd 1
    buf      resb 12

section .text
    global _start
_start:
    ; leia n  → sys_read(stdin, buf, 12) + parse ASCII→int
    mov eax, 3
    mov ebx, 0
    mov ecx, buf
    mov edx, 12
    int 0x80
    ; (parse omitido pra brevidade)

    mov dword [fat], 1
    mov dword [contador], 1

.loop_0:
    mov eax, [contador]
    mov ebx, [n]
    cmp eax, ebx
    jge .fim_loop_0

    mov eax, [contador]
    inc eax
    mov [contador], eax

    mov eax, [fat]
    imul eax, [contador]
    mov [fat], eax

    jmp .loop_0
.fim_loop_0:
    ; escreva fat (conversão int→ASCII + sys_write)
    ; ...
    mov eax, 1
    xor ebx, ebx
    int 0x80
```

**Terminal (sessão):**
```
5
120
[exit code: 0 — 0.07s]
```

### B. `PtyExecutionStrategy` — esqueleto de referência (Python)

```python
import asyncio
import json
import docker
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    exit_code: int
    duration_ms: int
    timed_out: bool


class ExecutionStrategy(ABC):
    @abstractmethod
    async def execute(self, binary_dir: str, ws, timeout_s: int) -> ExecutionResult:
        ...


class PtyExecutionStrategy(ExecutionStrategy):
    """
    Spawns a docker container with TTY attached and bridges its stdio to a
    WebSocket connection. Implements the Strategy pattern from the GoF playbook.
    """

    def __init__(self, image: str = "simples-runner:latest"):
        self.image = image
        self.client = docker.from_env()

    async def execute(self, binary_dir: str, ws, timeout_s: int) -> ExecutionResult:
        container = self.client.containers.run(
            image=self.image,
            # qemu-i386-static emula o binário x86 — funciona em hosts x86_64 e ARM64
            command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
            volumes={binary_dir: {"bind": "/sandbox", "mode": "ro"}},
            network_mode="none",
            mem_limit="128m",
            memswap_limit="128m",
            cpu_quota=50000,
            pids_limit=64,
            read_only=True,
            tmpfs={"/tmp": "size=8m"},
            user="65534:65534",
            cap_drop=["ALL"],
            stdin_open=True,
            tty=True,
            detach=True,
        )

        sock = container.attach_socket(
            params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}
        )
        sock._sock.setblocking(False)

        loop = asyncio.get_event_loop()
        start = loop.time()

        async def pty_to_ws():
            while True:
                try:
                    data = await loop.run_in_executor(None, sock._sock.recv, 4096)
                    if not data:
                        break
                    await ws.send(json.dumps({"type": "stdout", "data": data.decode("utf-8", errors="replace")}))
                except BlockingIOError:
                    await asyncio.sleep(0.01)

        async def ws_to_pty():
            async for message in ws:
                msg = json.loads(message)
                if msg["type"] == "stdin":
                    sock._sock.sendall(msg["data"].encode("utf-8"))
                elif msg["type"] == "stop":
                    container.kill(signal="SIGTERM")
                    break

        try:
            await asyncio.wait_for(
                asyncio.gather(pty_to_ws(), ws_to_pty()),
                timeout=timeout_s,
            )
            timed_out = False
        except asyncio.TimeoutError:
            container.kill(signal="SIGTERM")
            await asyncio.sleep(1)
            container.kill(signal="SIGKILL")
            timed_out = True

        result = container.wait(timeout=2)
        container.remove(force=True)

        return ExecutionResult(
            exit_code=result["StatusCode"],
            duration_ms=int((loop.time() - start) * 1000),
            timed_out=timed_out,
        )
```

> **Nota:** o trecho acima é referência didática. A implementação final lida com edge cases (socket fechado abruptamente, container que não inicia, race conditions no `wait`).

### C. Variáveis de ambiente (`.env.example`)

```bash
# Supabase
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings

# Limits
EXEC_TIMEOUT_S=10
COMPILE_TIMEOUT_S=15
MAX_CODE_KB=64
RUNS_PER_MINUTE=30

# Sandbox
SANDBOX_IMAGE=simples-runner:latest

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### D. Glossário

| Termo | Definição |
|---|---|
| **PTY** | Pseudo-terminal — par master/slave do kernel Linux que emula um terminal real para o processo |
| **xterm.js** | Biblioteca JavaScript que renderiza um emulador de terminal no browser (mesma do VS Code) |
| **NASM** | Netwide Assembler — montador de assembly x86 |
| **ELF** | Executable and Linkable Format — formato de binário do Linux |
| **JWT** | JSON Web Token — token de autenticação assinado |
| **RLS** | Row-Level Security — policies do Postgres que filtram linhas por usuário |
| **Sticky session** | Mecanismo do load balancer que mantém um cliente sempre no mesmo backend |
| **Sandbox** | Ambiente isolado onde código não-confiável roda com limites |

### E. Referências

- [PRD do compilador SIMPLES](https://www.notion.so/344a6259575b81098b28f3235354d86b) — gramática EBNF completa, mapeamento SIMPLES→NASM
- [TanStack Start docs](https://tanstack.com/start/latest)
- [Supabase Auth docs](https://supabase.com/docs/guides/auth)
- [xterm.js docs](https://xtermjs.org/)
- [Monaco Editor docs](https://microsoft.github.io/monaco-editor/)
- [Docker security best practices](https://docs.docker.com/engine/security/)
- [Flask-Sock](https://flask-sock.readthedocs.io/)
- [Oracle Cloud Always Free](https://www.oracle.com/cloud/free/)
- [Ampere A1 Compute](https://www.oracle.com/cloud/compute/arm/)
- [terraform-oci-ampere-a1 (módulo Ampere oficial)](https://github.com/AmpereComputing/terraform-oci-ampere-a1)
- [qemu-user-static no Debian](https://wiki.debian.org/QemuUserEmulation)

### F. Terraform — Provisionamento OCI Ampere A1

Esqueleto mínimo para subir a VM de produção. Coloca em `terraform/main.tf`. Substitui o passo manual do console (§14.7.1) — recomendado para qualquer ambiente que precise ser recriado.

```hcl
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

variable "tenancy_ocid"     { type = string }
variable "user_ocid"        { type = string }
variable "fingerprint"      { type = string }
variable "private_key_path" { type = string }
variable "region"           { type = string  default = "sa-saopaulo-1" }
variable "compartment_ocid" { type = string }
variable "ssh_public_key"   { type = string }

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# --- Network ---

resource "oci_core_vcn" "simples" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "simples-online-vcn"
  dns_label      = "simples"
}

resource "oci_core_internet_gateway" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-igw"
}

resource "oci_core_route_table" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.simples.id
  }
}

resource "oci_core_security_list" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # SSH — restringir ao seu IP em produção
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 22  max = 22 }
  }
  # HTTP (redirect para HTTPS via nginx)
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 80  max = 80 }
  }
  # HTTPS
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 443 max = 443 }
  }
}

resource "oci_core_subnet" "simples" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.simples.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "simples-public-subnet"
  route_table_id      = oci_core_route_table.simples.id
  security_list_ids   = [oci_core_security_list.simples.id]
  prohibit_public_ip_on_vnic = false
}

# --- Compute (Always Free Ampere A1) ---

data "oci_core_images" "ubuntu_2204_arm" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "simples" {
  availability_domain = data.oci_identity_availability_domain.ad.name
  compartment_id      = var.compartment_ocid
  display_name        = "simples-online"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 2     # Always Free permite até 4
    memory_in_gbs = 12    # Always Free permite até 24
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_2204_arm.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.simples.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(file("${path.module}/cloud-init.yaml"))
  }
}

data "oci_identity_availability_domain" "ad" {
  compartment_id = var.tenancy_ocid
  ad_number      = 1
}

output "public_ip" {
  value = oci_core_instance.simples.public_ip
}
```

E um `cloud-init.yaml` mínimo no mesmo diretório, que executa o bootstrap de §14.7.3 automaticamente na primeira boot:

```yaml
#cloud-config
package_update: true
package_upgrade: true

write_files:
  - path: /etc/iptables/rules.v4.simples
    content: |
      # Liberar 80/443 — adicionado pelo cloud-init
      -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
      -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

runcmd:
  # Liberar firewall do host
  - iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
  - iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
  - netfilter-persistent save

  # Docker Engine + Compose v2 (ARM64)
  - install -m 0755 -d /etc/apt/keyrings
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  - chmod a+r /etc/apt/keyrings/docker.asc
  - echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu jammy stable" > /etc/apt/sources.list.d/docker.list
  - apt-get update
  - apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  - usermod -aG docker ubuntu
```

**Comandos**:

```bash
cd terraform
terraform init
terraform plan  -var-file="oci.tfvars"
terraform apply -var-file="oci.tfvars"

# Após apply, conectar:
ssh ubuntu@$(terraform output -raw public_ip)
```
