"""
Adobe Sign Dashboard Test Runner.

Orchestrates database health checks, date range validation, and user list synchronization
for the Adobe Sign API integration.

This module handles:
- Business logic (empty data checks, validation)
- Exception handling (catches all custom exceptions)
- Pipeline-level logging
"""
import logging
from datetime import datetime, timedelta
from typing import List, Tuple

import test_api as api
import test_database as db
from test_exceptions import AppError, APIError, DatabaseError, AuthError

# Module-level constants
SECRETS_FOLDER: str = "client_secret/"
USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}test_user_list_v03.txt"

# Default date range (should be read from DB in production)
DEFAULT_LAST_DATE_RANGE_END: str = "2026-03-01T00:00:00Z"
#DEFAULT_LAST_DATE_RANGE_END: str = "2026-04-15T00:00:00Z"


def _configure_logging() -> None:
    """Configure logging format once at startup."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("tests/logs/test_log.log")
    file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s — %(message)s",
        handlers=[console_handler, file_handler]
    )


def compute_search_date_range(last_end_date_str: str) -> Tuple[str, str]:
    """Compute the 7-day search date range from the last end date.

    Args:
        last_end_date_str: ISO format date string of the previous range end.

    Returns:
        Tuple of (new_start_range_date_str, new_range_end_date_str).
    """
    start_date: datetime = datetime.fromisoformat(last_end_date_str)
    end_date: datetime = start_date + timedelta(days=7)
    end_date_str: str = f"{end_date.date()}T00:00:00Z"
    # logging.getLogger(__name__).debug(f"Computed date range: {last_end_date_str} to {end_date_str}")
    logger.debug(f"Computed date range: {last_end_date_str} to {end_date_str}")
    return last_end_date_str, end_date_str


def validate_range_in_past(range_end_date_str: str) -> bool:
    """Validate that the search range end date is in the past.

    Args:
        range_end_date_str: ISO format date string of the range end.

    Returns:
        True if range end is in the past, False otherwise.
    """
    today: datetime = datetime.today()
    naive_end_date: datetime = datetime.fromisoformat(
        range_end_date_str.replace("T00:00:00Z", " 00:00:00")
    )

    if today >= naive_end_date:
        # logging.getLogger(__name__).info(f"Search range validated - end date: {naive_end_date}")
        logger.info(f"Search range validated - end date: {naive_end_date}")
        return True

    logging.critical(
        f"Range end date {naive_end_date} is in the future - reschedule execution"
    )
    return False


def test_run_user_sync_process(db_module) -> None:
    """Test function to load test data into DB.

    Args:
        db_module: Database module with user list operations.
    """
    # TEST DATA: Load user list from file
    user_list: List[dict] = db_module.test_convert_txt_to_list(TEST_USER_LIST_FILENAME)
    # logging.getLogger(__name__).debug(f"Loaded {len(user_list)} users from file")
    logger.debug(f"Loaded {len(user_list)} users from file")

    # Transform dictionary keys to match table schema
    transformed_user_list: List[dict] = db_module.test_transform_user_list_keys(user_list)
    # logging.getLogger(__name__).info(f"Transformed {len(transformed_user_list)} user records")
    logger.info(f"Transformed {len(transformed_user_list)} user records")

    # Insert new users by email key
    db_module.insert_new_items_by_email_key(transformed_user_list)
    # logging.getLogger(__name__).debug("User sync process completed")
    logger.debug("User sync process completed")


def test_main() -> int:
    """Main entry point for the test runner.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    global logger
    logger = logging.getLogger(__name__)
    _configure_logging()
    
    logger.info("Starting test_main execution")

    try:
        # Compute search date range
        last_end_date: str = DEFAULT_LAST_DATE_RANGE_END
        _, range_end_str = compute_search_date_range(last_end_date)

        # Validate date range is in the past
        if not validate_range_in_past(range_end_str):
            logger.error("Date range validation failed - exiting")
            return 1

        # Fetch users from Adobe Sign API
        all_user_list: List[dict] = api.fetch_all_users()
        logger.info(f"Fetched {len(all_user_list)} users from Adobe Sign API")

        # Business condition: handle empty user list
        if not all_user_list:
            logger.warning("No users fetched from API - pipeline aborted")
            return 1

        # Transform API response keys to DB schema
        transformed_user_list: List[dict] = db.transform_user_list_keys(all_user_list)
        logger.debug(f"Transformed {len(transformed_user_list)} user records")

        # Insert only new users (not in existing email list)
        db.insert_new_items_by_email_key(transformed_user_list)

        # Backup: save to file
        with open(TEST_USER_LIST_FILENAME, "w") as file:
            file.write(f"{all_user_list}")

        logger.info("Test runner completed successfully")
        return 0

    except AuthError as e:
        logger.error(f"Authentication failed: {e}")
        return 1
    except APIError as e:
        logger.error(f"API error: {e}")
        return 1
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return 1
    except AppError as e:
        logger.error(f"Application error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code: int = test_main()
    logging.info(f"Exit code: {exit_code}")
    exit(exit_code)