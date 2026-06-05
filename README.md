# Simples Editor

Plataforma web para ensino de programacao com a linguagem SIMPLES — escreva, compile e execute codigo direto no navegador, sem instalar nada.

![Simples Editor](docs/screenshots/placeholder.png)

---

## Funcionalidades

- **Editor Monaco** com syntax highlight customizado para 27 palavras-chave da linguagem SIMPLES
- **Tema dark** profissional (`simples-dark`) com cores otimizadas para leitura de codigo
- **Layout 3 paineis** resizable: editor, saida NASM, terminal interativo
- **Compilador integrado**: `simplesc` traduz SIMPLES → NASM → executavel
- **Execucao interativa**: programas com `leia` funcionam via WebSocket + PTY
- **Sandbox seguro**: execucao isolada em container Docker (`--cap-drop=ALL`, `--read-only`, `--network=none`)
- **CI/CD**: GitHub Actions com 4 jobs paralelos (lint, test, build, smoke)

---

## Screenshots

### Editor com syntax highlight
<!-- Substituir por screenshot real: docs/screenshots/editor.png -->
![Editor](docs/screenshots/placeholder.png)

*27 palavras-chave em ciano com negrito, numeros em laranja, strings em amarelo, comentarios em verde italico.*

### Painel NASM
<!-- Substituir por screenshot real: docs/screenshots/nasm.png -->
![NASM](docs/screenshots/placeholder.png)

*Saida do compilador `simplesc` exibida no painel direito em tempo real.*

### Terminal interativo com `leia`
<!-- Substituir por screenshot real: docs/screenshots/terminal.png -->
![Terminal](docs/screenshots/placeholder.png)

*Terminal xterm.js com comunicacao bidirecional via WebSocket.*

### Tratamento de erros
<!-- Substituir por screenshot real: docs/screenshots/error.png -->
![Erro](docs/screenshots/placeholder.png)

*Erros de compilacao exibidos como markers vermelhos no Monaco Editor.*

### CI/CD Pipeline
<!-- Substituir por screenshot real: docs/screenshots/ci.png -->
![CI](docs/screenshots/placeholder.png)

*GitHub Actions com 4 jobs paralelos: frontend, backend, docker-stack, smoke.*

---

## Demo Video

[![Simples Editor Demo](docs/screenshots/placeholder.png)](docs/demo.mp4)

> Roteiro de gravacao: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)

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

| Documento | Descricao |
|---|---|
| [SPRINTS.md](SPRINTS.md) | Planejamento das 6 sprints |
| [PROGRESS.md](PROGRESS.md) | Checklist de progresso das issues |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia de contribuicao |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Guia de deploy Oracle Cloud Ampere A1 |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | Roteiro para video de demonstracao |
| [docs/APRESENTACAO.md](docs/APRESENTACAO.md) | Roteiro da apresentacao final |
| [docs/RETROSPECTIVA.md](docs/RETROSPECTIVA.md) | Retrospectiva da equipe |
| [docs/INSTRUCTIONS_DEV.md](docs/INSTRUCTIONS_DEV.md) | Instrucoes para desenvolvimento |

---

## Stack

- **Frontend**: React, TypeScript, Monaco Editor, xterm.js, Vite
- **Backend**: Python, Flask, flask-sock, gevent, gunicorn, structlog
- **Infra**: Docker, Docker Compose, Nginx, GitHub Actions
- **Seguranca**: Supabase Auth, sandbox Docker, rate limiting, Prometheus

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
