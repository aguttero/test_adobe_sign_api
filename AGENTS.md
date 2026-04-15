# Project: Adobe Sign Dashboard

## Stack
- Python 3.13+, SQLAlchemy 2.0+, SQLite
- Adobe Sign REST API (shard: na1)

## Module Structure (verified)
- `main.py` — orchestration entry point (sparse stub)
- `models.py` — User table definition only
- `database.py` — SQLAlchemy engine setup only
- `api.py` — token refresh + test code that writes to file

## Testing
Tests use **test-prefixed modules** in `tests/` folder — not pytest:
```bash
cd tests && python test_main.py      # runs with test_database, test_models
cd tests && python test_api.py    # runs api tests
```
- Test DB: `tests/data/test_01.db`
- Test logs: `tests/logs/test_log.log`
- Credentials: `client_secret/test_user_list.txt`

## Critical Conventions
- **Run from `tests/`**: imports `test_models` and `test_database` as test-prefixed modules
- Credentials via `.env` (root) + `client_secret/` folder
- Token file: `client_secret/adbe_dev_token.txt` (written by test run)
- DB URL in tests: `sqlite:///tests/data/test_01.db`

## Security
- NEVER read/modify: `.env`, `client_secret/`, `data/*.db`, `logs/`
- NEVER log credential values

## Dependencies
```bash
pip install -r sqlalch_api_reqs.txt
```

## Developer Commands
```bash
cd tests && python test_main.py    # main test runner
cd tests && python test_api.py    # api token refresh test
```

## Important Notes
- `log_reader.py` doesn't exist yet
- Root modules are incomplete scaffolding — real logic is in `tests/` copies
- `.gitignore` excludes: `.env`, `client_secret/`, `data/`, `logs/`, `*.db`, `*.log`
