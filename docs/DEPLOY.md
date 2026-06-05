# Guia de Deploy — Oracle Cloud Ampere A1 com Dominio Proprio

> Sprint 6 — Deploy em producao com TLS valido e dominio `*.edu.br`

---

## Pre-requisitos

- Conta Oracle Cloud com acesso a instancia Ampere A1 (Free Tier)
- Dominio registrado (ex: `simples.example.edu.br`)
- Acesso ao painel DNS do provedor de dominio
- Docker e Docker Compose instalados na VM

---

## 1. Provisionar VM na Oracle Cloud

```bash
# Criar instancia Ampere A1 (4 OCPUs, 24 GB RAM — Free Tier)
# Via console: Compute > Instances > Create Instance
#   Image: Ubuntu 24.04
#   Shape: Ampere (ARM)
#   OCPUs: 4
#   Memory: 24 GB
#   Boot volume: 100 GB
```

Apos criacao, anotar o **IP publico** da instancia.

---

## 2. Configurar DNS (Dominio proprio)

No painel do provedor de dominio, criar registro A:

```
Tipo: A
Nome: simples
Valor: <IP_PUBLICO_DA_VM>
TTL: 3600
```

Para dominio com `*.edu.br`:

```
Tipo: A
Nome: simples
Valor: <IP_PUBLICO_DA_VM>
TTL: 3600
```

Verificar propagacao:
```bash
dig simples.example.edu.br +short
# Deve retornar o IP da VM
```

---

## 3. Preparar VM

```bash
# Conectar via SSH
ssh ubuntu@<IP_DA_VM>

# Instalar Docker
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
newgrp docker

# Clonar repositorio
git clone https://github.com/GrouwBer/SimplesEditor.git
cd SimplesEditor
```

---

## 4. Configurar Certificado TLS

### Opcao A: Certbot + Let's Encrypt (recomendado)

```bash
# Instalar certbot
sudo apt-get update
sudo apt-get install -y certbot

# Gerar certificado (standalone — liberar portas 80/443 antes)
sudo certbot certonly --standalone -d simples.example.edu.br

# Copiar certificados para o projeto
sudo cp /etc/letsencrypt/live/simples.example.edu.br/fullchain.pem nginx/certs/
sudo cp /etc/letsencrypt/live/simples.example.edu.br/privkey.pem nginx/certs/
sudo chown $USER:$USER nginx/certs/*.pem
```

### Opcao B: Certificado auto-assinado (desenvolvimento)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem \
  -subj "/CN=simples.example.edu.br"
```

---

## 5. Configurar Variaveis de Ambiente

```bash
# Criar .env
cat > .env << 'EOF'
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=<sua-anon-key>
SUPABASE_JWT_SECRET=<seu-jwt-secret>
EOF
```

---

## 6. Build e Deploy

```bash
# Build das imagens
docker compose -f docker-compose.yml build

# Iniciar servicos
docker compose -f docker-compose.yml up -d

# Verificar status
docker compose ps
docker compose logs backend | tail -20
```

---

## 7. Verificar Deploy

```bash
# Health check
curl -k https://simples.example.edu.br/api/health
# Deve retornar: {"status":"ok"}

# Frontend
curl -k https://simples.example.edu.br | grep "<!DOCTYPE html>"
# Deve retornar HTML

# Testar redirect HTTP → HTTPS
curl -I http://simples.example.edu.br
# Deve retornar: 301 Moved Permanently → https://...
```

---

## 8. Configurar Renovacao Automatica do Certificado

```bash
# Adicionar ao crontab
sudo crontab -e

# Adicionar linha:
0 3 * * * certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/simples.example.edu.br/fullchain.pem /home/ubuntu/SimplesEditor/nginx/certs/ && cp /etc/letsencrypt/live/simples.example.edu.br/privkey.pem /home/ubuntu/SimplesEditor/nginx/certs/ && docker compose -f /home/ubuntu/SimplesEditor/docker-compose.yml restart nginx"
```

---

## 9. Monitoramento

```bash
# Logs
docker compose logs -f

# Metricas (interno apenas)
curl http://localhost:5000/metrics

# Status dos containers
docker compose ps
```

---

## Resumo da Configuracao Atual

| Componente | Configuracao |
|---|---|
| Dominio | `simples.example.edu.br` |
| TLS | Let's Encrypt (renovacao automatica) |
| HTTP → HTTPS | Redirect 301 (nginx) |
| Portas | 80 (HTTP), 443 (HTTPS) |
| Certificados | `nginx/certs/fullchain.pem`, `nginx/certs/privkey.pem` |
| Nginx config | `nginx/nginx.conf` (server blocks HTTP + HTTPS) |
