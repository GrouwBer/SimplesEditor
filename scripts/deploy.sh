#!/usr/bin/env bash
# deploy.sh — Deploy automatizado para Oracle Cloud Ampere A1
# Uso: ./scripts/deploy.sh <dominio> [branch]
# Exemplo: ./scripts/deploy.sh simples.example.edu.br dev

set -euo pipefail

DOMAIN="${1:-simples.example.edu.br}"
BRANCH="${2:-dev}"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

echo "=== Simples Editor — Deploy ==="
echo "Dominio: $DOMAIN"
echo "Branch: $BRANCH"
echo ""

# 1. Verificar pre-requisitos
command -v docker >/dev/null 2>&1 || { echo "Erro: Docker nao instalado"; exit 1; }

# 2. Verificar .env
if [ ! -f "$ENV_FILE" ]; then
    echo "Erro: $ENV_FILE nao encontrado. Crie a partir de .env.example"
    exit 1
fi

# 3. Verificar certificados TLS
if [ ! -f "nginx/certs/fullchain.pem" ] || [ ! -f "nginx/certs/privkey.pem" ]; then
    echo "Aviso: Certificados TLS nao encontrados."
    echo "Gerando certificado auto-assinado temporario..."
    mkdir -p nginx/certs
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout nginx/certs/privkey.pem \
      -out nginx/certs/fullchain.pem \
      -subj "/CN=$DOMAIN" 2>/dev/null
    echo "Certificado auto-assinado gerado."
    echo "Para producao, use certbot (veja docs/DEPLOY.md)."
fi

# 4. Pull latest
echo "Atualizando codigo (branch: $BRANCH)..."
git pull origin "$BRANCH" 2>/dev/null || echo "  (repositorio local, pulando git pull)"

# 5. Build
echo "Build das imagens Docker..."
docker compose -f "$COMPOSE_FILE" build --pull

# 6. Deploy
echo "Iniciando servicos..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" up -d

# 7. Aguardar healthcheck
echo "Aguardando backend ficar saudavel..."
for i in $(seq 1 30); do
    if curl -sk "https://localhost/api/health" 2>/dev/null | grep -q '"status": "ok"'; then
        echo "Backend saudavel!"
        break
    fi
    sleep 2
    if [ "$i" -eq 30 ]; then
        echo "Timeout: backend nao respondeu."
        docker compose -f "$COMPOSE_FILE" logs backend
        exit 1
    fi
done

# 8. Verificar frontend
echo "Verificando frontend..."
if curl -sk "https://localhost" 2>/dev/null | grep -q "<!DOCTYPE html>"; then
    echo "Frontend OK!"
else
    echo "Aviso: frontend nao esta servindo HTML"
fi

echo ""
echo "=== Deploy concluido! ==="
echo "Acesse: https://$DOMAIN"
echo "Health: https://$DOMAIN/api/health"
echo ""
echo "Para monitorar:"
echo "  docker compose -f $COMPOSE_FILE logs -f"
echo "  docker compose -f $COMPOSE_FILE ps"
