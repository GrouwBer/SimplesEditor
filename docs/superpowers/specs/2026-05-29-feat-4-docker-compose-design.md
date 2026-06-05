# Design: Docker Compose (dev + prod parity) — feat/4

Date: 2026-05-29
Issue: #4 — chore(devops): definir docker-compose com nginx, frontend e backend

## Objetivo
Fornecer docker-compose com paridade de produção e um override para desenvolvimento com hot-reload (frontend + backend). Facilitar "docker compose up" para alunos rodarem localmente.

## Serviços
- nginx: reverse proxy e, em produção, serve frontend estático.
- frontend: React (npm start em dev, build em prod).
- backend: Flask (flask run --reload em dev, gunicorn em prod).

## Arquitetura
- docker-compose.yml contém configuração de produção (imagens/builds).
- docker-compose.override.yml ativa bind-mounts, comandos de dev e expõe portas para hot-reload.
- nginx usa conf diferente em dev (proxy para frontend:3000) e prod (serve /usr/share/nginx/html).

## Dockerfiles (resumo)
- frontend/Dockerfile: multi-stage build (node:18 -> nginx:alpine).
- backend/Dockerfile: python:3.11-slim, gunicorn para produção.

## Comandos de uso (dev)
- docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
- Acessar: http://localhost:8080 (nginx proxy para frontend dev server)

## Healthchecks
- backend: /api/health deve responder {status: "ok"}
- CI/Actions: build images e rodar smoke tests contra nginx

## Arquivos adicionados
- docker-compose.yml
- docker-compose.override.yml
- frontend/Dockerfile
- backend/Dockerfile
- nginx/default.conf
- nginx/default.dev.conf
- docs/INSTRUCTIONS_DEV.md

## Notas
- .env e secrets não devem ser commitados. Use env_file e CI secrets.
- Recomenda-se WSL2 no Windows para melhor performance de bind-mounts.

'
