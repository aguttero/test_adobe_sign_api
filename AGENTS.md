# Project: Adobe Sign Signature Dashboard

## Overview
Weekly signature status dashboard. Tracks ~1,500 documents/month via Adobe Sign API. Exports to dashboard.csv. Stack: Python 3.11+, SQLAlchemy, SQLite, REST API.

## Directory Structure
- **tests/** — Active development modules (test_main.py, test_api.py, test_auth.py, test_database.py, test_models.py, test_utils.py, test_exceptions.py)
- **tests/data/** — SQLite database (`test_01.db`)
- **tests/old_modules/** — Ignore
- **tests/zscrappping_code/** — Ignore
- **src/** — Ignore
- **client_secret/** — Contains credentials (token files, .env should go here)

## Critical Commands
```bash
# Run the main script
python tests/test_main.py

# Run specific test (if pytest is set up)
pytest tests/test_<module>.py
```

## Module Architecture (load order)
1. **test_exceptions.py** — Custom exceptions: AppError, DatabaseError, APIError, AuthError
2. **test_utils.py** — Pure helper functions
3. **test_models.py** — SQLAlchemy models: User (table: user_account), Agreement, SyncHistory
4. **test_auth.py** — TokenManager class with auto-refresh, 300s buffer before expiry
5. **test_database.py** — All DB ops via SQLAlchemy (not sqlite3 directly)
6. **test_api.py** — Adobe Sign HTTP calls, uses TokenManager internally
7. **test_main.py** — Orchestration only

## Database Schema
- **user_account** table: id, email (unique), adbe_sign_id (unique), group_id, first_name, last_name, job_area, job_title, status, last_sync (date)
- **agreement** table: id, agreement_id (unique), display_date, name, type, status, workflow_id, group_id, created_date, last_event_date, user_id (FK)
- **sync_history** table: id, run_date, range_start, range_end, agreements_found, sync_ok

## Key Functions
- **test_api.fetch_all_users()** — Paginated fetch from Adobe Sign /users endpoint, returns list of dicts with 'email' and 'id'
- **test_database.get_existing_emails()** — Returns list of emails in User table
- **test_database.filter_new_users(existing_emails, input_list)** — Filters input to only new users by email
- **test_database.bulk_insert_list(table, input_list)** — Bulk insert into table
- **test_database.test_transform_user_list_keys(input_list)** — Transforms API format ('email', 'id') to DB format ('email', 'adbe_sign_id'), normalizes email to lowercase

## Credentials
All credentials come from environment variables via `dotenv_values(".env")`:
- CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
- .env file location: project root or `./client_secret/`

## Token Management
- TokenManager in test_auth.py handles auto-refresh
- Refresh happens 300s before actual expiry
- First network call happens on first get_token() call (lazy initialization)

## Coding Conventions
- Type hints required everywhere
- Custom exceptions wrap library exceptions (never leak raw sqlite3/requests errors)
- test_database.py only does DB ops (no API calls)
- test_api.py only does HTTP (no business logic on empty results)
- main.py handles all business condition checks (empty lists, etc.)
- keep main() in main.py lean and readable

## Logging Rules

### Log Level Assignment
| Level | When to Use |
|-------|-------------|
| **DEBUG** | Internal function detail (bytes read, rows parsed, pagination cursors) |
| **INFO** | Business milestones (token refreshed, rows inserted, pipeline complete, users fetched, agreements found) |
| **WARNING** | Recoverable unexpected condition (empty result, skipped step, user invalid) |
| **ERROR** | Caught failure, handled (auth failed, API unreachable, DB error) |
| **CRITICAL** | Unrecoverable failure, app cannot continue |

### Key Principles
- **Functions** log operational detail at DEBUG/INFO level
- **test_main() function in main.py** logs pipeline-level outcomes at INFO/WARNING/ERROR
- **Never log the same event in both the function and the caller**
- test_utils.py provides logging helpers: `log_debug()`, `log_info()`, `log_warning()`, `log_error()`, `log_critical()`

### Module Logging Responsibilities
- `test_exceptions.py` — No logging (pure exception classes)
- `test_utils.py` — No logging (pure helper functions)
- `test_models.py` — No logging (pure data structures)
- `test_auth.py` — DEBUG for token operations, ERROR for failures
- `test_database.py` — DEBUG for DB operations, INFO for inserts, ERROR for failures
- `test_api.py` — DEBUG for HTTP details, INFO for API milestones, ERROR for failures
- `test_monitor.py` — DEBUG for I/O operations, WARNING for read failures
- `test_main.py` — INFO for business outcomes, WARNING for skipped steps, ERROR/CRITICAL for failures

### Logging Format
```python
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s — %(message)s"
)
```

## What NOT to Modify
- Files in `src/`
- Files in `tests/old_modules/`
- Files in `tests/bkup/`
- Files in `tests/zscrappping_code/`
- Credentials (hardcode in code - always use os.getenv() or dotenv_values)

## Existing Agent Guidelines
See `.opencode/agents/python_coder.md` for detailed coding rules (naming, exception handling, logging format).