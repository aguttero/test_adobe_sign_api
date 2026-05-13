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
from datetime import date, datetime, timedelta
from typing import List, Tuple

import test_api as api
import test_database as db
from test_exceptions import AppError, APIError, DatabaseError, AuthError


# Module-level constants
SECRETS_FOLDER: str = "client_secret/"
USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}test_user_list_mock_v02.txt"


# Default date range (should be read from DB in production)
DEFAULT_LAST_DATE_RANGE_END: str = "2026-04-12T00:00:00Z"
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


def search_new_agreements(
    user_email: str,
    #user_adbe_sign_id: str,
    date_range_start: str,
    date_range_end: str
) -> List[dict]:
    """Search agreements for a given user within a date range and persist to DB.

    Args:
        user_email: Email address of the agreement owner.
        user_adbe_sign_id: Adobe Sign user ID of the agreement owner.
        date_range_start: Start date for search (ISO format).
        date_range_end: End date for search (ISO format).

    Returns:
        List of agreement dictionaries.
    """
    logger.info(f"Searching agreements for {user_email} from {date_range_start} to {date_range_end}")

    # Search agreements via API
    agreement_list: List[dict] = api.search_agreements(
        user_email=user_email,
        # user_adbe_sign_id=user_adbe_sign_id,
        date_range_start=date_range_start,
        date_range_end=date_range_end
    )
    logger.info(f"Found {len(agreement_list)} agreements for {user_email}")

    # Get user from DB to associate agreements
    user = db.get_user_by_email(user_email)
    if user is None:
        logger.error(f"User {user_email} not found in database")
        return []

    # Persist agreements to DB
    agreements_inserted = db.insert_agreements(agreement_list, user.id)
    logger.info(f"Inserted {agreements_inserted} agreements for {user_email}")

    return agreement_list


def search_agreements_for_users(
    user_list: List[dict],
    date_range_start: str,
    date_range_end: str
) -> Tuple[int, int, int]:
    """Search agreements for multiple users and persist to DB.

    Args:
        user_list: List of user dictionaries with 'email' and 'adbe_sign_id'.
        date_range_start: Start date for search (ISO format).
        date_range_end: End date for search (ISO format).

    Returns:
        Tuple of (total_users_searched, users_with_zero_agreements, users_with_agreements).
    """
    total_users: int = len(user_list)
    users_with_zero: int = 0
    users_with_agreements: int = 0
    total_agreements: int = 0

    logger.info(f"Searching agreements for {total_users} users")

    for user in user_list:
        user_email = user.get("email", "")
        # user_adbe_sign_id = user.get("adbe_sign_id", "")

        #if not user_email or not user_adbe_sign_id:
        if not user_email:
            logger.warning(f"Skipping user with missing email or adbe_sign_id")
            continue

        try:
            agreements = search_new_agreements(
                user_email=user_email,
                # user_adbe_sign_id=user_adbe_sign_id,
                date_range_start=date_range_start,
                date_range_end=date_range_end
            )

            if len(agreements) == 0:
                users_with_zero += 1
            else:
                users_with_agreements += 1
                total_agreements += len(agreements)

        except Exception as e:
            logger.error(f"Error searching agreements for {user_email}: {e}")
            continue

    # Log summary statistics
    logger.info(f"Total users searched: {total_users}")
    logger.info(f"Users with zero agreements: {users_with_zero}")
    logger.info(f"Users with agreements: {users_with_agreements}")
    logger.info(f"Total agreements found: {total_agreements}")

    return total_users, users_with_zero, users_with_agreements


def sync_agreements_for_all_users(date_range_start: str, date_range_end: str) -> Tuple[int, int, int]:
    """Search and persist new agreements for all users in the database.

    Executes after user sync is complete. Fetches all users from DB and searches
    agreements for each user within the given date range.

    Args:
        date_range_start: Start date for agreement search (ISO format).
        date_range_end: End date for agreement search (ISO format).

    Returns:
        Tuple of (total_users, users_with_zero_agreements, users_with_agreements).
    """
    logger.info("Starting agreement sync for all users in database")

    # Get all users from database
    ## PROD CODE
    all_users: List[dict] = db.get_all_users()

    ## TEST CODE
    # from dotenv import dotenv_values
    # config = dotenv_values('.env')
    # TEST_DEV_USER_EMAIL = config.get("TEST_DEV_USER_EMAIL")

    # test_usr_email = TEST_DEV_USER_EMAIL
    # date_range_start = "2025-01-01T00:00:00Z"
    # date_range_end = "2026-01-10T00:00:00Z"

    # all_users: List[dict] =[
    #             {"email": TEST_DEV_USER_EMAIL, "adbe_sign_id": "some user id"}
    # ]
    ## END TEST CODE

    logger.info(f"Found {len(all_users)} users in database to search agreements for")

    if not all_users:
        logger.warning("No users found in database - skipping agreement sync")
        return 0, 0, 0

    # Search agreements for each user
    result = search_agreements_for_users(all_users, date_range_start, date_range_end)
    total_searched, users_with_zero, users_with_agr = result

    logger.info(f"Agreement sync completed: {total_searched} users searched, "
              f"{users_with_zero} with zero agreements, {users_with_agr} with agreements")

    return total_searched, users_with_zero, users_with_agr


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
        last_end_date_str: str = DEFAULT_LAST_DATE_RANGE_END
        _, new_end_date_str = compute_search_date_range(last_end_date_str)

        # Validate date range is in the past
        if not validate_range_in_past(new_end_date_str):
            logger.error("Date range validation failed - exiting")
            return 1

        ## PROD CODE commented for TEST
        #Fetch users from Adobe Sign API
        all_user_list: List[dict] = api.fetch_all_users()
        logger.info(f"Fetched {len(all_user_list)} users from Adobe Sign API")

        ## TEST CODE
        # all_user_list = [{'email': ' Test9@eMail.com ','first_name': 'Charlie','last_name': 'Update','status': 'test','id': 'updated_user_id_09'},{'email': ' Test10@eMail.com ','first_name': 'Charlie','last_name': 'Update','status': 'test','id': 'updated_user_id_10'}]

        # Business condition: handle empty user list
        if not all_user_list:
            logger.warning("No users fetched from API - pipeline aborted")
            return 1

        # Transform API response keys to DB schema
        transformed_user_list: List[dict] = db.transform_user_list_keys(all_user_list)
        logger.debug(f"Transformed {len(transformed_user_list)} user records")

        # Insert only new users (not in existing email list)
        db.insert_new_items_by_email_key(transformed_user_list)


        # === SEARCH AND PERSIST AGREEMENTS FOR ALL USERS ===
        # This executes after the user fetch/insert task is completed
        # Use the computed date range for agreement search
        _, agreement_end_str = compute_search_date_range(last_end_date_str)
        total_users, users_with_zero, users_with_agr = sync_agreements_for_all_users(
            date_range_start=last_end_date_str,
            date_range_end=agreement_end_str
        )
        logger.info(f"Agreement sync finished: {total_users} users, {users_with_zero} zero, {users_with_agr} with agreements")

        # Backup: save to file
        # with open(TEST_USER_LIST_FILENAME, "w") as file:
        #     file.write(f"{all_user_list}")

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