"""
Adobe Sign Dashboard Test Runner.

Orchestrates database health checks, date range validation, and user list synchronization
for the Adobe Sign API integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import test_api as api
import test_database as db

# Module-level constants
SECRETS_FOLDER: str = "client_secret/"
USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}test_user_list_v02.txt"

# TODO: Replace hardcoded date with config or DB value
DEFAULT_LAST_DATE_RANGE_END: str = "2026-03-01T00:00:00Z"

### LOGGER CONFIG ###
console_handler: logging.StreamHandler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler: logging.FileHandler = logging.FileHandler("tests/logs/test_log.log")
file_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(module)s:%(funcName)s - %(message)s',
    handlers=[console_handler, file_handler]
)

logger: logging.Logger = logging.getLogger(__name__)
logger.debug("Logging configured successfully")
### END LOGGER CONFIGURATION ###



# TODO refactor/move to test_utils.py
def compute_search_date_range(last_end_date_str: str) -> tuple[str, str]:
    """
    Compute the 7-day search date range from the last end date.

    Args:
        last_end_date_str: ISO format date string of the previous range end.

    Returns:
        Tuple of (new_start_range_date_str, new_range_end_date_str).
    """
    start_date: datetime = datetime.fromisoformat(last_end_date_str)
    end_date: datetime = start_date + timedelta(days=7)
    end_date_str: str = f"{end_date.date()}T00:00:00Z"
    logger.debug(f"Computed date range: {last_end_date_str} to {end_date_str}")
    return last_end_date_str, end_date_str


# TODO refactor/move to test_utils.py
def validate_range_in_past(range_end_date_str: str) -> bool:
    """
    Validate that the search range end date is in the past.

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
        logger.info(f"Search range validated - end date: {naive_end_date}")
        return True

    logger.critical(
        f"Range end date {naive_end_date} is in the future - reschedule execution"
    )
    return False


def test_run_user_sync_process(db_module) -> None:
    """
    Test function to load test data into DB 
    Execute the user list synchronization process.

    Args:
        db_module: Database module with user list operations.
    """
    # Fetch user email and user adobe_sign_id from Adobe Sign API /users endpoint
    

    # TEST DATA Load user list from file
    user_list: list[dict] = db_module.test_convert_txt_to_list(TEST_USER_LIST_FILENAME)
    logger.debug(f"Loaded {len(user_list)} users from file")

    # Transform dictionary keys to match table schema
    transformed_user_list: list[dict] = db_module.test_transform_user_list_keys(user_list)
    logger.info(f"Transformed {len(transformed_user_list)} user records")

    # Insert new users by email key
    db_module.insert_new_items_by_email_key(transformed_user_list)
    logger.debug("User sync process completed")


def test_main() -> int:
    """
    Main entry point for the test runner.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    logger.debug("Starting test_main execution")

    # Import modules after logger config
    logger.debug("Modules imported successfully")

    ## TEST Validate database health
    # if not validate_db_health(db):
    #     logger.error("Database health check failed - exiting")
    #     return 1

    # Compute search date range
    # TODO: Read last_end_date_str from DB Exec Log instead of hardcoding
    last_end_date: str = DEFAULT_LAST_DATE_RANGE_END
    _, range_end_str = compute_search_date_range(last_end_date)

    # Validate date range is in the past
    if not validate_range_in_past(range_end_str):
        logger.error("Date range validation failed - exiting")
        return 1

    # TEST API fetch token
    # api.test_fetch_token()

    # TEST API fetch users
    all_user_list = api.fetch_all_users()
    logger.info(f"Fetched {len(all_user_list)} users from Adobe Sign API")

    # Transform API response keys to DB schema
    transformed_user_list = db.test_transform_user_list_keys(all_user_list)
    logger.debug(f"Transformed {len(transformed_user_list)} user records")

    # Insert only new users (not in existing email list)
    db.insert_new_items_by_email_key(transformed_user_list)

    # TEST API save to file (backup)
    with open (TEST_USER_LIST_FILENAME, "w") as file:
        file.write(f"{all_user_list}")

    logger.debug("Test runner completed successfully")
    return 0


if __name__ == "__main__":
    exit_code: int = test_main()
    logger.info(f"Exit code: {exit_code}")
    exit(exit_code)