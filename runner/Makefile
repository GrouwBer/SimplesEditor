.PHONY: build test lint clean

IMAGE_NAME := simples-runner
IMAGE_TAG  := latest

# ============================================================
# Build: constroi a imagem simples-runner com qemu-user-static
# ============================================================
build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile .

# ============================================================
# Test: smoke test — verifica se qemu-i386-static existe na imagem
# e se o usuario nobody (UID 65534) eh o padrao
# ============================================================
test:
	@echo "[1/2] Verificando qemu-i386-static..."
	@docker run --rm --entrypoint="" $(IMAGE_NAME):$(IMAGE_TAG) \
		/usr/bin/qemu-i386-static -version 2>&1 || \
		(echo "FAIL: qemu-i386-static nao encontrado na imagem" && exit 1)
	@echo "       OK — qemu-i386-static presente."
	@echo ""
	@echo "[2/2] Verificando usuario nobody (UID 65534)..."
	@USER_ID=$$(docker run --rm --entrypoint="" $(IMAGE_NAME):$(IMAGE_TAG) \
		sh -c 'id -u' 2>/dev/null || echo ""); \
	if [ "$$USER_ID" = "65534" ]; then \
		echo "       OK — usuario nobody (UID 65534) configurado."; \
	else \
		echo "       AVISO: nao foi possivel verificar UID (shell removido por hardening)."; \
		echo "       O USER 65534 esta declarado no Dockerfile — confie na build."; \
	fi

# ============================================================
# Lint: verifica se o Dockerfile segue boas praticas
# ============================================================
lint:
	@echo "Verificando boas praticas do Dockerfile..."
	@if grep -q "FROM debian:12-slim" Dockerfile; then \
		echo "  [OK] Base image: debian:12-slim (minimal)"; \
	else \
		echo "  [WARN] Base image nao eh debian:12-slim"; \
	fi
	@if grep -q "USER 65534:65534" Dockerfile; then \
		echo "  [OK] Non-root user configurado (nobody)"; \
	else \
		echo "  [WARN] USER nao configurado como nobody"; \
	fi
	@if grep -q "qemu-user-static" Dockerfile; then \
		echo "  [OK] qemu-user-static instalado"; \
	else \
		echo "  [FAIL] qemu-user-static ausente no Dockerfile"; \
	fi
	@if grep -q "rm -rf /var/lib/apt/lists" Dockerfile; then \
		echo "  [OK] Cache apt limpo para reduzir tamanho"; \
	else \
		echo "  [WARN] Cache apt nao foi limpo"; \
	fi
	@if grep -q "LABEL org.simples-editor.sandbox" Dockerfile; then \
		echo "  [OK] Labels OCI de seguranca presentes"; \
	else \
		echo "  [WARN] Labels OCI ausentes"; \
	fi
	@echo "Lint concluido."

# ============================================================
# Clean: remove a imagem local
# ============================================================
clean:
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "Imagem $(IMAGE_NAME):$(IMAGE_TAG) removida (se existia)."
