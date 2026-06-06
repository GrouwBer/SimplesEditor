#!/usr/bin/env bash
# renew-certs.sh — Renovacao automatica de certificados Let's Encrypt
# Chamado pelo crontab diariamente as 3h da manha.
#
# Requer: certbot instalado, dominio configurado, projeto em /home/ubuntu/SimplesEditor

set -euo pipefail

PROJECT_DIR="${SIMPLES_PROJECT_DIR:-/home/ubuntu/SimplesEditor}"
DOMAIN="${1:-simples.example.edu.br}"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
NGINX_CERTS="$PROJECT_DIR/nginx/certs"

certbot renew --quiet --post-hook "
    cp $CERT_DIR/fullchain.pem $NGINX_CERTS/ &&
    cp $CERT_DIR/privkey.pem $NGINX_CERTS/ &&
    docker compose -f $PROJECT_DIR/docker-compose.yml restart nginx
"
