"""
Adobe Sign Dashboard Orchestration.

This module orchestrates the entire data pipeline for the Adobe Sign dashboard.
It handles initialization, date range preparation, data synchronization (groups, users, agreements, workflows),
and error handling. It ensures that pipeline steps are executed in the correct order
and that exceptions are caught and logged appropriately.
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Tuple, Optional

import models
import api
import database as db
import utils
import monitor
from exceptions import AppError, APIError, DatabaseError, AuthError


# Module-level constants
SECRETS_FOLDER: str = "client_secret/"
USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME: str = f"{SECRETS_FOLDER}test_user_list_mock_v02.txt"


# Default date range (should be read from DB in production)
DEFAULT_LAST_DATE_RANGE_END: str = "2020-01-11T00:00:00Z"
#DEFAULT_LAST_DATE_RANGE_END: str = "2026-04-15T00:00:00Z"
DAYS_TO_ADD_TO_RANGE: int = 2

# Init Module-level logger
logger = logging.getLogger(__name__)

def _configure_logging() -> None:
    """Configure logging format once at startup."""
    
    now = datetime.now()
    filestamp = now.strftime("%Y%m%d_%H_%M")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(f"logs/{filestamp}_new.log")
    file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(module)s.%(funcName)s — %(message)s",
        handlers=[console_handler, file_handler]
    )
    logger.debug("Finalized logging init and config")


def initialize_app():
    """Initialize application settings like logging and return core process variables."""
    _configure_logging()

    # Track execution timing and setup initial state
    run_id: str = utils.generate_run_id()
    start_time: datetime = utils.get_current_timestamp()
    initial_agreement_count: int = 0
    sync_history_id: int = 0
    
    logger.debug(f"run_id={run_id}, start_time={start_time}")
    return run_id, start_time, initial_agreement_count, sync_history_id


def compute_search_date_range(last_end_date_str: str) -> Tuple[str, str]:
    """Compute the 7-day search date range from the last end date.

    Args:
        last_end_date_str: ISO format date string of the previous range end.

    Returns:
        Tuple of (new_start_range_date_str, new_range_end_date_str).
    """
    start_date: datetime = datetime.fromisoformat(last_end_date_str)
    end_date: datetime = start_date + timedelta(days=DAYS_TO_ADD_TO_RANGE)
    end_date_str: str = f"{end_date.date()}T00:00:00Z"
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
    # Parse the date string, making it naive for comparison with today's date
    naive_end_date: datetime = datetime.fromisoformat(
        range_end_date_str.replace("T00:00:00Z", " 00:00:00")
    )

    if today >= naive_end_date:
        logger.info(f"Search range validated - end date: {naive_end_date}")
        return True

    logging.critical(
        f"Range end date {naive_end_date} is in the future - reschedule execution"
    )
    return False

def prepare_date_range(last_sync_date_str: str) -> Tuple[str | None, str | None]:
    """Computes and validates the date range for the current sync.

    Args:
        last_sync_date_str: The end date of the last successful sync, used as the start for the current range.

    Returns:
        A tuple containing the start and end date strings for the current sync range.
        Returns None for both if validation fails.
    """
    # Compute the date range for the current sync
    new_start_date_str, new_end_date_str = compute_search_date_range(last_sync_date_str)

    # Validate that the computed date range is in the past
    if not validate_range_in_past(new_end_date_str):
        # Error is already logged within validate_range_in_past
        return None, None

    logger.info(f"Date range prepared: {new_start_date_str} to {new_end_date_str}")
    return new_start_date_str, new_end_date_str

def sync_groups() -> int:
    """Fetches, parses, and upserts group data into the database. Returns 0 on success, 1 on failure."""
    try:
        api_groups_list: list[dict] = api.fetch_all_groups()
        ## TODO validate all_grp_list len > 0
        logger.debug(f"Group list len: {len(api_groups_list)} TODO: NEED TO VALIDATE THIS IS > 0")

        parsed_groups = models.parse_groups(api_groups_list)
        db.upsert_groups(parsed_groups)
        logger.info("Group synchronization completed successfully.")
        return 0 # Success code

    except Exception as e:
        logger.error(f"Failed to sync groups: {e}")
        return 1 # Failure code

def sync_users() -> int:
    """Fetches, transforms, and inserts new user data. Returns 0 on success, 1 on failure."""
    try:
        # Fetch users from Adobe Sign API
        api_user_list: List[dict] = api.fetch_all_users()

        # Business condition: handle empty user list
        if not api_user_list:
            logger.warning("No users fetched from API - skipping user sync.")
            return 0 # No users found, but not a failure of the sync process itself

        # Transform API response keys to DB schema
        transformed_user_list: List[dict] = db.transform_user_list_keys(api_user_list)
        logger.debug(f"Transformed {len(transformed_user_list)} user records")

        # Insert only new users (not in existing email list)
        db.insert_new_items_by_email_key(transformed_user_list)
        logger.info("User synchronization completed successfully.")
        return 0 # Success code

    except APIError as e:
        logger.error(f"API error during user sync: {e}")
        # Specific handling for invalid user could be added here if needed
        return 1 # Failure code
    except Exception as e:
        logger.error(f"An unexpected error occurred during user sync: {e}")
        return 1 # Failure code

def sync_agreements() -> int:
    """Searches for and persists new agreements for all users in the database.

    This function is called after user synchronization is complete.
    It iterates through users, searches for agreements within the prepared date range,
    and persists the found agreements and their signers to the database.

    Returns:
        0 for success, 1 for failure.
    """
    logger.info("Starting agreement sync for all users in database")

    # Get all users from database (exclude INVALID_USER status)
    all_users: List[dict] = db.get_all_users(exclude_status="INVALID_USER")

    if not all_users:
        logger.warning("No users found in database - skipping agreement sync")
        return 0 # No users to sync agreements for, not a failure

    logger.info(f"Found {len(all_users)} users in database to search agreements for")

    # Search agreements for each user
    total_users, users_with_zero, users_with_agr = sync_agreements_for_users(all_users, date_range_start, date_range_end)
    logger.info(f"Agreement sync finished: {total_users} users searched, "
              f"{users_with_zero} with zero agreements, {users_with_agr} with agreements")
    
    return 0 # Success code

def main() -> int:
    """Main entry point for the application orchestrates the sync process."""
    
    # Init Logger config and run and time stamps
    run_id, start_time, initial_agreement_count, sync_history_id = initialize_app()

    # Prepare the date range for the sync process
    date_range_start, date_range_end = prepare_date_range(DEFAULT_LAST_DATE_RANGE_END)
    
    if date_range_start is None or date_range_end is None:
        # Date range preparation failed, error already logged in prepare_date_range
        return 1

    try:
        # Insert SyncHistory record at the start of the run
        try:
            sync_history_id = db.insert_sync_history(
                run_id=run_id,
                range_start=date_range_start,
                range_end=date_range_end
            )
            logger.info(f"Starting main execution - Run ID: {run_id}")
            logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.critical(f"Failed to create sync history record: {e} - exiting")
            return 1    

        # Get initial agreement count for rollback tracking
        try:
            initial_agreement_count = db.get_agreement_count()
            logger.debug(f"Initial agreement count: {initial_agreement_count}")
        except Exception as e:
            logger.warning(f"Could not get initial agreement count: {e}")

    
        # === EXECUTE PIPELINE STEPS ===
        group_sync_status = sync_groups()
        user_sync_status = sync_users()
        agreement_sync_status = sync_agreements()

        # Determine overall success status based on individual step statuses
        overall_sync_ok = (group_sync_status == 0 and 
                           user_sync_status == 0 and 
                           agreement_sync_status == 0)

        # === FINALIZE === 
        # Calculate elapsed time
        end_time: datetime = utils.get_current_timestamp()
        hours, minutes, seconds = utils.calculate_elapsed_time(start_time, end_time)
        elapsed_str: str = utils.format_elapsed_time(hours, minutes, seconds)
        end_time_str: str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get final agreement count
        final_agreement_count = db.get_agreement_count()
        agreements_found = final_agreement_count - initial_agreement_count
        
        # Update SyncHistory with overall success status
        log_file_path = "logs/test_log.log"
        log_lines = monitor.read_recent_log_lines(log_file_path)
        log_counts = monitor.count_log_records_by_level(log_lines)
        
        try:
            db.update_sync_history(
                sync_id=sync_history_id,
                agreements_found=agreements_found,
                sync_ok=overall_sync_ok, # Reflect the actual success status of all sync steps
                elapsed_time=elapsed_str,
                end_time=end_time_str,
                error_qty=log_counts.get("ERROR", 0),
                warning_qty=log_counts.get("WARNING", 0),
                critical_qty=log_counts.get("CRITICAL", 0)
            )
        except Exception as e:
            logger.warning(f"Failed to update sync history: {e}")
        
        logger.info(f"Main execution completed. Overall status: {'Success' if overall_sync_ok else 'Failed'}")
        logger.info(f"End time: {end_time_str}")
        logger.info(f"Elapsed time: {elapsed_str}")
        logger.info(f"Agreements found: {agreements_found}")
        logger.info(f"Run ID: {run_id} - {'COMPLETED' if overall_sync_ok else 'FAILED'}")
        
        return 0 if overall_sync_ok else 1

    except AuthError as e:
        logger.error(f"Authentication failed: {e}")
        _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        return 1
    except APIError as e:
        logger.error(f"API error: {e}")
        _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        return 1
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        return 1
    except AppError as e:
        logger.error(f"Application error: {e}")
        _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        return 1

def dev_main () -> int:
    # Init Logger config and run and time stamps
    run_id, start_time, initial_agreement_count, sync_history_id = initialize_app()
    logger.info(f"DEV_MAIN START")

    # Prepare the date range for the sync process
    date_range_start, date_range_end = prepare_date_range(DEFAULT_LAST_DATE_RANGE_END)
    logger.debug (f"date_range_start={date_range_start}, date_range_end={date_range_end}")


    logger.debug(f"DEV_MAIN END")
    return 0

if __name__ == "__main__":
    exit_code: int = dev_main()
    logging.info(f"Logging Exit code: {exit_code}")
    print (f"exit code: {exit_code}")
    exit(exit_code)
