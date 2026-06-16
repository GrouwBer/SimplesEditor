.PHONY: test clean check-tools

# Backend tests do SimplesEditor
# Executa pytest com verbose e stop-on-first-failure

test:
	pip install -r requirements.txt > /dev/null 2>&1 || true
	PYTHONPATH=. python -m pytest test_app.py -v

# Verifica se a toolchain de compilacao esta completa
# simplesc (compilador), nasm (assembler), i686-linux-gnu-ld (linker cross 32-bit)
check-tools:
	@echo "=== Verificando toolchain de compilacao ==="
	@echo ""
	@# simplesc
	@if command -v simplesc >/dev/null 2>&1; then \
		echo "[OK] simplesc   : $$(simplesc 2>&1 | head -1 || echo 'instalado')"; \
	else \
		echo "[FAIL] simplesc : NAO ENCONTRADO — necessario para compilar SIMPLES -> NASM"; \
		exit 1; \
	fi
	@# nasm
	@if command -v nasm >/dev/null 2>&1; then \
		echo "[OK] nasm       : $$(nasm --version 2>&1 | head -1)"; \
	else \
		echo "[FAIL] nasm     : NAO ENCONTRADO — necessario para gerar codigo objeto"; \
		exit 1; \
	fi
	@# i686-linux-gnu-ld (linker cross-target 32-bit)
	@if command -v i686-linux-gnu-ld >/dev/null 2>&1; then \
		echo "[OK] i686-ld    : $$(i686-linux-gnu-ld --version 2>&1 | head -1)"; \
	else \
		echo "[FAIL] i686-ld  : NAO ENCONTRADO — necessario para linkar ELF i386"; \
		echo "       Instale: apt-get install binutils-i686-linux-gnu"; \
		exit 1; \
	fi
	@echo ""
	@echo "Toolchain OK — pronta para compilar SIMPLES -> NASM -> ELF i386."

# Limpa caches de bytecode Python
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
