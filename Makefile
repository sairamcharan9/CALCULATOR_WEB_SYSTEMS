.PHONY: help web cli playground test test-unit test-cli test-api test-e2e docker-up docker-down clean

help:
	@echo "======================================================================"
	@echo "Advanced Dual-Mode Calculator Makefile Helper"
	@echo "======================================================================"
	@echo "Available targets:"
	@echo "  web          - Start the FastAPI Web Server (http://127.0.0.1:8000)"
	@echo "  cli          - Launch the interactive CLI REPL session"
	@echo "  playground   - Launch an interactive Python shell with app modules loaded"
	@echo "  test         - Run the complete test suite with coverage reporting"
	@echo "  test-unit    - Run isolated unit tests"
	@echo "  test-cli     - Run CLI integration tests"
	@echo "  test-api     - Run FastAPI integration tests"
	@echo "  test-e2e     - Run Playwright browser end-to-end tests"
	@echo "  docker-up    - Build and orchestrate full stack via Docker Compose"
	@echo "  docker-down  - Tear down Docker Compose containers"
	@echo "  clean        - Remove cached bytecode and test cache directories"
	@echo "======================================================================"

web:
	python main.py

cli:
	python main.py --cli

playground:
	python -i -c "import app; print('\n✨ Welcome to the Calculator interactive playground session!\nExplore the available modules under app/core, app/cli, and app/api.')"

test:
	pytest tests/unit tests/fastapi/integration tests/cli --cov=app --cov=main --cov-report=term-missing

test-unit:
	pytest tests/unit -v

test-cli:
	pytest tests/cli -v

test-api:
	pytest tests/fastapi/integration -v

test-e2e:
	TEST_URL=http://localhost:8000 pytest tests/fastapi/e2e -v

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	-rm -rf __pycache__ .pytest_cache
	-find . -type d -name "__pycache__" -exec rm -rf {} +
