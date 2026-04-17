# old_main.py v20240417am
"""
Adobe Sign Dashboard Test Runner.

Orchestrates database health checks, date range validation, and user list synchronization
for the Adobe Sign API integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

# Module-level constants
SECRETS_FOLDER: str = "client_secret/"
USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}test_user_list.txt"

# TODO: Replace hardcoded date with config or DB value
DEFAULT_LAST_DATE_RANGE_END: str = "2026-03-01T00:00:00Z"

# Logger configuration
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
    Execute the user list synchronization process.

    Args:
        db_module: Database module with user list operations.
    """
    # Fetch user email and user adobe_sign_id from Adobe Sign API /users endpoint
    

    # Load user list from file
    user_list: list[dict] = db_module.test_convert_txt_to_list(TEST_USER_LIST_FILENAME)
    logger.debug(f"Loaded {len(user_list)} users from file")

    # Transform dictionary keys to match table schema
    transformed_user_list: list[dict] = db_module.test_transform_user_list_keys(user_list)
    logger.info(f"Transformed {len(transformed_user_list)} user records")

    # Insert new users by email key
    db_module.insert_new_items_by_email_key(transformed_user_list)
    logger.debug("User sync process completed")


def fetch_and_persist_agreements(
    db_module,
    api_module,
    start_date_str: str,
    end_date_str: str
) -> tuple[int, int]:
    """
    Fetch agreements for all users and persist to database.
    
    Args:
        db_module: Database module with agreement operations.
        api_module: API module with search and mapping functions.
        start_date_str: ISO format start date for date range filter.
        end_date_str: ISO format end date for date range filter.
    
    Returns:
        Tuple of (users_processed, agreements_found).
    """
    # Get all users from DB
    users = db_module.get_all_users()
    logger.info(f"Processing agreements for {len(users)} users")
    
    total_agreements = 0
    
    for user in users:
        try:
            agreements = api_module.search_agreements_by_user(
                user_email=user.email,
                start_date=start_date_str,
                end_date=end_date_str
            )
            
            for agreement_dict in agreements:
                agreement_data = api_module.map_api_to_agreement(agreement_dict, user.id)
                db_module.upsert_agreement(agreement_data)
                total_agreements += 1
                
        except Exception as e:
            logger.error(f"Failed to process agreements for user {user.email}: {e}")
            continue
    
    logger.info(f"Agreement sync complete: {total_agreements} agreements from {len(users)} users")
    return len(users), total_agreements


def test_main() -> int:
    """
    Main entry point for the test runner.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    logger.debug("Starting test_main execution")

    # Import modules after logger config
    #import test_models as dbmodels
    #import test_database as db
    import test_api as api

    logger.debug("Modules imported successfully")

    # Validate database health
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

    # TEST fetch token
    api.test_fetch_token()


    # Fetch users from Adobe Sign API
    # try:
    #     all_user_list = []
    #     all_user_list = api.fetch_users()
    # except:
    #     #TODO handle errors, retry and notification
    #     pass

    # Test Process: Run user synchronization process
    # test_run_user_sync_process(db)

    
    # Fetch and persist agreements for all users
    # users_processed, agreements_found = fetch_and_persist_agreements(
    #     db_module=db,
    #     api_module=api,
    #     start_date_str=last_end_date,
    #     end_date_str=range_end_str
    # )
    # logger.info(f"Processed {users_processed} users, found {agreements_found} agreements")
    
    logger.debug("Test runner completed successfully")

    # TODO for each user in the Users table fetch agreements that match criteria: (status=SIGNED and createdDate in DateRange)
    # TODO persist agreements in DB 
    

    # TODO Run safe DB close procedure


    return 0


if __name__ == "__main__":
    exit_code: int = main()
    logger.info(f"Exit code: {exit_code}")
    exit(exit_code)