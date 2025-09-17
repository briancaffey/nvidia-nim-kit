# NVIDIA NIM Kit

A toolkit for NVIDIA NIM integration.

## Development Setup

1. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

4. Run the FastAPI server:
   ```bash
   uv run python nimkit/src/main.py
   ```

   Or using uvicorn directly:
   ```bash
   uv run uvicorn nimkit.src.main:app --reload
   ```

5. Access the API:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Testing

Run tests with uv:
```bash
uv run pytest
```

## Development Commands

- Install new dependencies: `uv add <package-name>`
- Install dev dependencies: `uv add --dev <package-name>`
- Update dependencies: `uv sync --upgrade`
- Run any command in the virtual environment: `uv run <command>`

## Project Structure

```
nimkit/
├── src/           # Source code
│   ├── main.py    # FastAPI application
│   └── __init__.py
├── test/          # Tests
│   ├── test_main.py
│   └── __init__.py
└── __init__.py
```
