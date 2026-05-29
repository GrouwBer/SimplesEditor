# Task List — Issue #5: Validar docker compose up do stack local

| Task ID | Description | Status | Verification Command |
|---|---|---|---|
| 1 | Criar branch feat/5 a partir da dev | DONE | `git branch` |
| 2 | Criar estrutura de compilador mock simples-compiler/ | DONE | Verificar Makefile e main.c |
| 3 | Criar configuração do nginx com suporte HTTP/HTTPS e certificados locais | DONE | `openssl x509 -text -noout -in nginx/certs/fullchain.pem` |
| 4 | Criar esqueleto do frontend (React + TS) e backend (Flask) com Dockerfiles | DONE | Verificar arquivos |
| 5 | Executar `docker compose up --build -d` e validar status do stack | DONE | `docker compose ps` |
| 6 | Validar resposta na rota http://localhost e endpoint de health check | DONE | `curl -f http://localhost/api/health` |
