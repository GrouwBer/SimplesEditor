# Simples Editor

Plataforma web para ensino de programacao com a linguagem SIMPLES — escreva, compile e execute codigo direto no navegador, sem instalar nada.

> Screenshots conceituais abaixo. Consulte [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) para o roteiro de demonstracao.

---

## Funcionalidades

- **Editor Monaco** com syntax highlight customizado para 27 palavras-chave da linguagem SIMPLES
- **Tema dark** profissional (`simples-dark`) com cores otimizadas para leitura de codigo
- **Layout 3 paineis** resizable: editor, saida NASM, terminal interativo
- **Compilador integrado**: `simplesc` traduz SIMPLES → NASM → executavel
- **Execucao interativa**: programas com `leia` funcionam via WebSocket + PTY
- **Sandbox seguro**: execucao isolada em container Docker (`--cap-drop=ALL`, `--read-only`, `--network=none`)
- **CI/CD**: GitHub Actions com 4 jobs paralelos (frontend, backend, docker-stack, smoke)

---

## Screenshots

| Cena | Descricao |
|---|---|
| ✅ Editor | Syntax highlight com 27 palavras-chave, numeros, strings, comentarios |
| ✅ Painel NASM | Saida do compilador `simplesc` no painel direito |
| ✅ Terminal | xterm.js com comunicacao bidirecional via WebSocket (`leia`) |
| ✅ Erros | Markers vermelhos no Monaco Editor |
| ✅ CI/CD | GitHub Actions: 4 jobs paralelos |

---

## Demo Video

Roteiro de gravacao completo em [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

---

## Arquitetura

```
┌─────────────┐    ┌──────────┐    ┌────────────────┐
│  Navegador   │────│  Nginx   │────│  Frontend (React)│
│  (Monaco,    │    │  :80/443 │    │  Monaco Editor   │
│   xterm.js)  │    └──────────┘    └────────────────┘
└─────────────┘                          │
                                         │ REST + WebSocket
                                  ┌──────┴──────────┐
                                  │  Backend (Flask) │
                                  │  + simplesc      │
                                  └──────┬──────────┘
                                         │ docker-py
                                  ┌──────┴──────────┐
                                  │  Sandbox Docker  │
                                  │  (QEMU i686)     │
                                  └─────────────────┘
```

| Componente | Tecnologia |
|---|---|
| Frontend | React 18 + TypeScript + Monaco Editor + xterm.js |
| Backend | Flask 3 + flask-sock + gevent + gunicorn |
| Compilador | simplesc (C) → NASM → ld (i686) |
| Proxy | Nginx 1.25 (Alpine) com TLS |
| Sandbox | Docker + QEMU user-static |
| CI/CD | GitHub Actions (4 jobs paralelos) |
| Auth | Supabase |

---

## Como rodar

### Pre-requisitos

- Docker e Docker Compose
- Node.js 18+ (apenas para desenvolvimento local)

### Desenvolvimento (hot-reload)

```bash
git clone https://github.com/GrouwBer/SimplesEditor.git
cd SimplesEditor
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

Acesse: http://localhost:8080

### Producao

```bash
docker compose -f docker-compose.yml up -d --build
```

Acesse: http://localhost:80 (HTTP) ou https://localhost:443 (HTTPS)

### Testes

```bash
# Backend
cd backend && python -m pytest -q

# Frontend
cd frontend && npm ci && npm run lint && npm test
```

---

## Documentacao

| Documento | Descricao | Status |
|---|---|---|
| [SPRINTS.md](SPRINTS.md) | Planejamento das 6 sprints | ✅ |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuicao | ✅ |
| [docs/INSTRUCTIONS_DEV.md](docs/INSTRUCTIONS_DEV.md) | Instrucoes para desenvolvimento | ✅ |
| [PROGRESS.md](PROGRESS.md) | Checklist de progresso das issues | ✅ |
| [docs/RETROSPECTIVA.md](docs/RETROSPECTIVA.md) | Retrospectiva da equipe | ✅ |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Guia de deploy Oracle Cloud | ✅ |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | Roteiro para video de demonstracao | ✅ |
| [docs/APRESENTACAO.md](docs/APRESENTACAO.md) | Roteiro da apresentacao final | ✅ |

---

## Stack

- **Frontend**: React, TypeScript, Monaco Editor, xterm.js, Vite
- **Backend**: Python, Flask, flask-sock, gevent, gunicorn, structlog
- **Infra**: Docker, Docker Compose, Nginx, GitHub Actions
- **Seguranca**: Supabase Auth, sandbox Docker, rate limiting (30 exec/min), metricas Prometheus

---

## Seguranca

> **Aviso**: Nunca commitar secrets (chaves, tokens, senhas) no repositorio.
> Use o arquivo `.env` (incluido no `.gitignore`) para variaveis de ambiente locais.
> Consulte `.env.example` para as variaveis necessarias.

---

## Contribuindo

1. Crie uma branch: `git checkout -b feat/minha-feature`
2. Commit: `git commit -m "feat: descricao (closes #N)"`
3. Push: `git push -u origin feat/minha-feature`
4. Abra um PR para `dev`

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

---

## Licenca

MIT © 2026 Simples Editor Team
