# Contributing

1. Fork and create a feature branch.
2. `pip install -e ".[dev,media]"`
3. Make your change. Keep providers behind their base class.
4. `make check` — runs `ruff` and `pytest`.
5. Open a PR describing what changed and how you tested it.

## Conventions

- Python 3.11+, type hints everywhere, Pydantic models for data crossing stage boundaries.
- No secrets in code or YAML — use `.env`.
- Tests must not hit real APIs; use fixtures or mocks.
- Commit messages: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
