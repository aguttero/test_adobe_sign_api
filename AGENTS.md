# Project: Adobe Sign Signature Dashboard

## Project Overview
Weekly signature status dashboard. Tracks ~1,500 documents/month via
Adobe Sign API. Exports to dashboard.csv. Stack: Python 3.11+, SQLAlchemy, SQLite, REST API calls.

## Module Structure
- `main.py` — orchestration, scheduler, entry point
- `models.py`- all DB Table definitions and relationships
- `database.py` — all SQLite read/write operations
- `api.py` — Adobe Sign API calls and response parsing
- `log_reader.py` — parses logs, generates alerts

## Coding Standards
- Use Python type hints on all function signatures
- Docstrings on every function (one-line summary + params)
- No hardcoded credentials — always load from .env via python-dotenv
- Functions should do one thing (max ~30 lines)
- Handle all API exceptions explicitly, never bare `except:`

## Security Rules
- NEVER read or modify: .env, credentials/, data/*.db, logs/
- NEVER suggest printing or logging credential values
- NEVER inline API keys or tokens in code

## Database Conventions
- All DB access goes through db_ops.py — no raw sqlite3 calls in other modules
- Use parameterized queries only (no string formatting in SQL)
- Always close connections in a finally block or use context managers

## Error Handling & Logging
- Use Python's built-in `logging` module (not print statements)
- Log levels: DEBUG for API responses, INFO for operations, WARNING for
  retries, ERROR for failures
- Log format: timestamp [level] module:function - message

## Testing
- Run tests with: `pytest tests/`
- Each module has a corresponding test file: test_database.py, etc.
- Mock all external API calls in tests (never hit real Adobe Sign in tests)

## Dependencies
- Install with: `pip install -r sqlalch_api_reqs.txt`
- Key packages: requests, python-dotenv, pytest, schedule, SQLAlchemy

## Developer Commands

```bash
python /tests/test_main.py
```
