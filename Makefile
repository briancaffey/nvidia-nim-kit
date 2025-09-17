.PHONY: black test test-cov test-cov-html coverage-report

black:
	@echo "🎨 Formatting code with Black..."
	docker compose run --rm backend black . --line-length 88 --exclude .venv
	@echo "✅ Code formatting complete!"

test:
	@echo "🧪 Running pytest tests..."
	docker compose run --rm backend pytest
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running pytest tests with coverage..."
	docker compose run --rm backend pytest --cov=nimkit/src --cov-report=term-missing
	@echo "✅ Coverage tests complete!"

test-cov-html:
	@echo "🧪 Running pytest tests with HTML coverage report..."
	docker compose run --rm backend pytest --cov=nimkit/src --cov-report=html --cov-report=term-missing
	@echo "✅ HTML coverage report generated in htmlcov/ directory!"

coverage-report:
	@echo "📊 Generating coverage report..."
	docker compose run --rm backend coverage report
	@echo "✅ Coverage report complete!"
