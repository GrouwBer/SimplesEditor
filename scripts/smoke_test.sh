#!/usr/bin/env bash
set -euo pipefail

# Run docker compose (production)
docker compose -f docker-compose.yml up -d --build

# Wait for backend health
for i in {1..60}; do
  if curl -sS http://localhost:80/api/health | grep -q '"status": "ok"'; then
    echo "health ok"
    break
  fi
  echo "waiting for health... ($i)"
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "healthcheck timeout"
    docker compose down
    exit 1
  fi
done

# Basic smoke: homepage
if curl -sS http://localhost:80 | grep -q "<!DOCTYPE html>"; then
  echo "frontend ok"
else
  echo "frontend missing or not serving html"
  docker compose down
  exit 1
fi

# Tear down
docker compose down
