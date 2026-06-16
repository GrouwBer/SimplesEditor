.PHONY: test clean

# Backend tests do SimplesEditor
# Executa pytest com verbose e stop-on-first-failure

test:
	pip install -r requirements.txt > /dev/null 2>&1 || true
	PYTHONPATH=. python -m pytest test_app.py -v

# Limpa caches de bytecode Python
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
