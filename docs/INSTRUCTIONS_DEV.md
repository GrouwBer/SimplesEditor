# Development: docker compose (dev)

1. Instalar Docker / Docker Desktop (recomenda-se WSL2 no Windows)
2. Rodar:

   docker compose -f docker-compose.yml -f docker-compose.override.yml up --build

3. Acessar: http://localhost:8080 (nginx proxy para frontend dev server)

Notes:
- Para produção: docker compose -f docker-compose.yml up --build -d
- Não commit secrets; usar .env e CI secrets.
