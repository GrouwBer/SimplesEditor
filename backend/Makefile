.PHONY: test clean security-audit

# Backend tests do SimplesEditor
# Executa pytest com verbose e stop-on-first-failure

test:
	pip install -r requirements.txt > /dev/null 2>&1 || true
	PYTHONPATH=. python -m pytest test_app.py test_security.py -v

# Auditoria de seguranca do sandbox Docker
# Executa o script audit_sandbox.sh contra a imagem configurada
security-audit:
	@echo "=== Auditoria de Seguranca do Sandbox ==="
	@echo "Imagem: $${SANDBOX_IMAGE:-simples-runner:latest}"
	@if command -v docker >/dev/null 2>&1; then \
		echo "Docker disponivel — executando auditoria..."; \
		bash ../scripts/audit_sandbox.sh; \
	else \
		echo "Docker nao disponivel neste ambiente."; \
		echo "Para executar a auditoria localmente:"; \
		echo "  cd scripts && bash audit_sandbox.sh"; \
	fi

# Limpa caches de bytecode Python
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
