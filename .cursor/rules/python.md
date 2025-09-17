# Python Development Rules

- All python commands should be run through docker compose
- ALWAYS use `uv` as the package manager, never `pip`
- Use `uv add <package>` to add dependencies
- Use `uv run <command>` to run commands
- Source code lives in `nimkit/src/`
- Tests live in `nimkit/test/`
