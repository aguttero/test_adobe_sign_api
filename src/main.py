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
from dotenv import dotenv_values

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
DEFAULT_LAST_DATE_RANGE_END: str = "2025-11-01T00:00:00Z"
#DEFAULT_LAST_DATE_RANGE_END: str = "2026-04-15T00:00:00Z"
DAYS_TO_ADD_TO_RANGE: int = 61
# 2020, 366 days
days_per_year = {
    '2020': 366,
    '2021': 365,
    '2022': 365,
    '2023': 365,
    '2024': 366,
    '2025': 365,
    '2026': 365,
    '2027': 365,
    '2028': 366

}

# Storage Locations
storage_config = dotenv_values('.env')

STORAGE_FOLDER = storage_config.get("STORAGE_FOLDER") # "storage/"
JAD_PDF_FOLDER = storage_config.get("JAD_PDF_FOLDER") # "jad_pdf/"
JAD_TXT_FOLDER = storage_config.get("JAD_TXT_FOLDER") # "jad_txt/"
CONTRACT_PDF_FOLDER = storage_config.get("CONTRACT_PDF_FOLDER") # "con_pdf/"
CONTRACT_TXT_FOLDER = storage_config.get("CONTRACT_TXT_FOLDER") # "con_txt/"


# Init Module-level logger
logger = logging.getLogger(__name__)
now = datetime.now()
filestamp = now.strftime("%Y%m%d_%H_%M")
log_file_path = f"logs/{filestamp}.log"


def _configure_logging() -> None:
    """Configure logging format once at startup."""

    # MOVED THESE LINES TO # INIT Module-leve logger    
    # now = datetime.now()
    # filestamp = now.strftime("%Y%m%d_%H_%M")
    # log_file_path = f"logs/{filestamp}.log"

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)


    file_handler = logging.FileHandler(log_file_path)
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

def sync_groups() -> Optional[int]:
    """Fetches, parses, and upserts group data into the database. Returns quantuty of groups found on success or raises APP ERROR on failure."""
    try:
        api_groups_list: list[dict] = api.fetch_all_groups()

        if len(api_groups_list) == 0:
            logger.warning(f"Sync {len(api_groups_list)} groups")
            # determinar si raise APP ERROR
            return None

        parsed_groups = models.parse_groups(api_groups_list)
        db.upsert_groups(parsed_groups)
        logger.info(f"Group synchronization completed successfully. Parsed {len(parsed_groups)} groups")
        return len(parsed_groups)

    except Exception as e:
        logger.error(f"Failed to sync groups: {e}")
        raise AppError (f"APP ERROR: Failed to sync groups: {e}")


def sync_workflows() -> Optional[int]:
    """Fetches, parses, and upserts workflow data into the database. 
    
    Returns: quantity of workflows found on success or 
    
    Raises: APP ERROR on failure."""
    try:
        api_workflow_list: list[dict] = api.fetch_all_workflows()

        if len(api_workflow_list) == 0:
            logger.warning(f"Sync {len(api_workflow_list)} workflows")
            # Determine how to handle this situation
            raise AppError(f"APP ERROR: no workflows fetched")

        parsed_workflows = models.parse_workflows(api_workflow_list)
        
        ### TEST CODE ###
        # logger.debug(f"parsed_workflows:\n{parsed_workflows}")
        ### TEST CODE ###
       
        db.upsert_workflows(parsed_workflows)
        logger.info(f"Worklow synchronization completed successfully. Parsed {len(parsed_workflows)} workflows")
        return len(parsed_workflows)

    except Exception as e:
        logger.error(f"Failed to sync workflows: {e}")
        raise AppError (f"APP ERROR: Failed to sync workflows: {e}")

def sync_users() -> Optional[int]:
    """Fetches, transforms, and inserts new user data. Returns quantity of users found on success or raises APP ERROR on failure."""
    try:
        # Fetch users from Adobe Sign API
        api_user_list: List[dict] = api.fetch_all_users()
        logger.debug(f"api user list len={len(api_user_list)}")

        # Business condition: handle empty user list
        if len (api_user_list) == 0:
            logger.warning(f"Sync {len(api_user_list)} users")
            # determinar si raise APP ERROR
            return None

        # Transform API response keys to DB schema
        transformed_user_list: List[dict] = db.transform_user_list_keys(api_user_list)
        logger.debug(f"Transformed {len(transformed_user_list)} user records")

        # Insert only new users (not in existing email list)
        db.insert_new_items_by_email_key(transformed_user_list)
        logger.info("User synchronization completed successfully.")
        return len(api_user_list)

    except APIError as e:
        logger.error(f"API error during user sync: {e}")
        # Specific handling for invalid user could be added here if needed
        raise APIError (f"API ERROR: {e}", original_exc=e)
    except Exception as e:
        logger.error(f"An unexpected error occurred during user sync: {e}")
        raise AppError (f"APP ERROR: Failed to sync users: {e}")

def search_agreements_users( user_list: List[dict],
                            date_range_start: str,
                            date_range_end: str) -> Tuple[int, int, int]:
    """Search agreements for multiple users and persist to DB.

    Args:
        user_list: List of user dictionaries with 'email' and 'adbe_sign_id'.
        date_range_start: Start date for search (ISO format).
        date_range_end: End date for search (ISO format).

    Returns:
        Tuple of (total_users_searched, users_with_zero_agreements, users_with_agreements).
    """
    pass




def sync_agreements(date_range_start, date_range_end) -> Optional[int]:
    """Searches for and persists new agreements for all users in the database.

    This function is called after user synchronization is complete.
    It iterates through users, searches for agreements within the prepared date range,
    and persists the found agreements and their signers to the database.

    Returns:
        Quantity of agreements or raises App Error.
    """
    logger.info("Starting agreement sync for all users in database")
    logger.debug(f"date_range_start={date_range_start}, date_range_end= {date_range_end}")

    # Get all users from database (exclude INVALID_USER status) list of dict with email and adobe_id
    all_valid_users: List[dict] = db.get_all_users(exclude_status="INVALID_USER")

    if len(all_valid_users) == 0:
        logger.warning(f"Sync {len(all_valid_users)} users")
        raise AppError (f"APP ERROR: Found {len(all_valid_users)} valid users in DB")

    logger.info(f"Found {len(all_valid_users)} valid users in database to search agreements for")

    # Search and persist agreements and signers for each user
    # Output: total_users, users_with_zero, users_with_agr qty of new agreements
    ### TEST CODE ### LIST SPLIT TO LIMIT ITERATIONS
    #for user_dict in all_valid_users[:1]:
    ### TEST CODE ###

    for user_dict in all_valid_users:
        user_email = user_dict['email']
        
        ### TEST CODE ####
        # TO ASSIGN TEST USER from '.env'
        # from dotenv import dotenv_values
        # config = dotenv_values(".env")
        # user_email = config.get('TEST_DEV_USER_EMAIL2')
        #### TEST CODE ####

        user_sign_id = user_dict['adbe_sign_id']
        
        #### TEST CODE ####
        # logger.debug(f"user_email={user_email}, user_sign_id={user_sign_id}")
        #### TEST CODE ####
        
        # SKIP API SEARCH FOR TEST
        try:
            api_output = api.search_agreements_user(user_email, date_range_start, date_range_end)
        except APIError as e:
            # CHECK for INVALID_USER error 401
            if "INVALID_USER" in str(e):
                logger.debug(f"6 capturado e: {e}, str(e) = {str(e)}, stat_code={e.status_code}, original_exc={e.original_exc}")
                logger.warning(f"7 User {user_email} is invalid - marking in DB")
                db.update_user_status_by_email(user_email, "INVALID_USER")
            else:
                logger.error(f"8 API error searching agreements for {user_email}: {e}")
            continue

        #### TEST CODE ####
        ## TO SAVE API DATA TO TEST
        # with open ("src/data/api_fun_agmnt_test_api_out_0512_01.txt","w") as file:
        #     file_content = f"{api_output}"
        #     file.write(file_content)
        # logger.debug(f"wrote test file: {len(file_content)} chars")

        ## TO TEST IMPORTING DATA FROM FILE:
        # import ast
        # with open ("src/data/api_fun_agmnt_test_api_out.txt","r") as file:
        #     file_content = file.read()
        # logger.debug(f"read from file: {len(file_content)} chars")
        # test_api_output = ast.literal_eval(file_content)
        # logger.debug(f"OK Assign to list {len(test_api_output)} items")
        #### TEST CODE ####

        # get user id from DB
        user_instance = db.get_user_by_email(user_email)
        # logger.debug(f"user_instance={user_instance}")

        # OLD insert agreement
        insert_result = db.insert_agreements(api_output,user_instance.id)
        #insert_result = db.insert_agreements(test_api_output,user_instance.id)
        logger.info(f"Inserted {insert_result} agreements")
        
    # total_users, users_with_zero, users_with_agr = api.search_agreements(all_valid_users, date_range_start, date_range_end)
    # logger.info(f"Agreement sync finished: {total_users} users searched, {users_with_zero} with zero agreements, {users_with_agr} with agreements")
    
    return 999 # qty of new persisted agreements


def download_documents(date_range_start, date_range_end, agreement_type:str):
    """
    Downloads documents and approvers from api, saves to local storage and persists into database
    Returns: quantity of pdf documents stored
    Raises?
    """
    logger.debug(f"date_range_start= {date_range_start!r}, date_range_end= {date_range_end!r}")

    ### TEST CODE 1 ###
    # from dotenv import dotenv_values
    # config = dotenv_values(".env")
    # target_agreement_id = config.get("TEST_AGREEMENT_ID_01")
    # agreement_type = "JAD"
    ### TEST CODE 1 ###

    # FETCH AGREEMENT LIST FROM DB
    # Obtain list of agreements id to download from API
    target_wkflow_list = [6] # WFs 5,6 carry JAD process 
    # target_wkflow_list = [5,6] # WFs 5,6 carry JAD process 
    target_agreement_list = db.fetch_agrmnt_by_wkflow(date_range_start, date_range_end, target_wkflow_list)

    # ITERATE AGREEMENT LIST TO FETCH PDF FROM API, APPROVER INFO FROM API STORE and UPDATE DOC INDEX TABLE
    for agrmnt_id in target_agreement_list:
        counter = 0
        # ---DOWNLOAD AGREEMENT FROM API
        # api_pdf_bytes = api.download_agreement(agrmnt_id)

        # ---SAVE PDF TO FILE
        # STORE IN 'tmp_jad/agreement_id.pdf'
        # PENDING: Validate file does not exist
        # PENDING: Save as .tmp then validate downloaded ok then rename to .pdf

        # PROD CODE <---
        # target_file_path = f"{STORAGE_FOLDER}{JAD_PDF_FOLDER}{agrmnt_id}.pdf"
        # with open(target_file_path,"wb") as file:
        #     file.write(api_pdf_bytes)
        # logger.debug(f"Saved to local file agreement_id: {STORAGE_FOLDER}{JAD_PDF_FOLDER}{agrmnt_id}.pdf")


        # ---UPDATE DOCUMENT INDEX TABLE
        # db_file_status = "downloaded"
        # db.update_agrmnt_doc_status(agrmnt_id, agreement_type, db_file_status, JAD_PDF_FOLDER)

        # --- FETCH APPROVERS FROM API
        api_response = api.fetch_approvers(agrmnt_id)

        logger.debug(f"api_response= {api_response}")

        # --- UPDATE APPROVER TABLE



        #--- PARSE DOCUMENT TO TOKENS

        #--- SAVE TXT TO FILE

        #---UPDATE DOCUMENT INDEX TABLE
        # db_file_status = "parsed"
        # db.update_agrmnt_doc_parse_status(agrmnt_id,agreement_type, db_file_status, JAD_TXT_FOLDER)


        counter +=1


    logger.debug(f"Updated {counter} agreements")

    counter = 0
    
    # descargar file y Audit trail por separado
    # agregar a la tabla path del audit trail


    # db.update_db_storage_index(target_file_path,agreement_type,target_agreement_id)
    counter +=1

    return counter    


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
        except DatabaseError as e:
            logger.error(f"Initial agreement count failed: {e}. Caused by: {e.original_exc}")
            # Define Business decision to do next
            # fall back procedure
            return 1


    
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
                lookup_run_id=sync_history_id,
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
    # OK logger.debug (f"date_range_start={date_range_start}, date_range_end={date_range_end}")
    
    # This if is here to save the type error in Insert SyncHistory step
    if date_range_start is None or date_range_end is None:
        # Date range preparation failed, error already logged in prepare_date_range
        return 1

    # Insert SyncHistory record at the start of the run
    try:
        sync_history_id = db.insert_sync_history(
                    run_id=run_id,
                    range_start=date_range_start,
                    range_end=date_range_end
                )
        logger.info(f"Starting main execution - Run ID: {run_id} - Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    except DatabaseError as e:
        logger.critical(f"Failed to create sync history record: {e} Caused by: {e.original_exc} - exiting")
        # Define Business decision to do next
        # fall back procedure
        return 1   

    # Get initial agreement count for rollback tracking
    try:
        initial_agreement_count = db.get_agreement_count()
        logger.info(f"Rollback safety net init: Initial agreement count: {initial_agreement_count}")
    except DatabaseError as e:
        logger.critical(f"Could not get initial agreement count: {e}. Caused by: {e.original_exc} - exiting")
        # Define Business decision to do next
        # fall back procedure
        return 1

    # EXECUTE PIPELINE STEPS
    try:
        # GROUP SYNC
        # result_groups_sync = sync_groups()
        # logger.debug(f"Pipe 1. result_grp_sync={result_groups_sync}")
        # if not result_groups_sync:
        #     logger.warning(f"Synced {result_groups_sync} groups. - exiting")
        #     return 1
        
        # WORKFLOW SYNC
        # result_wkflow_sync = sync_workflows()
        # logger.debug(f"Pipe 2. result_wkflow_sync={result_wkflow_sync}")
        # if not result_wkflow_sync:
        #     logger.warning(f"Synced {result_wkflow_sync} groups. - exiting")
        #     return 1

        # USER SYNC
        # result_users_sync = sync_users()
        # logger.debug(f"Pipe 3. result_user_sync={result_users_sync}")
        # if not result_users_sync:
        #    logger.warning(f"Synced {result_users_sync} users. - exiting")
        #    return 1
        
        # AGREEMENT SYNC
        # result_agreement_sync = sync_agreements(date_range_start,date_range_end)
        # logger.debug(f"Pipe 4. result_agreement_sync={result_agreement_sync}")
        # if not result_agreement_sync:
        #     logger.warning(f"Synced {result_agreement_sync} groups. - exiting")
        #     return 1


        ### DOWNLOAD STAGE #####
        # ----- DOWNLOAD AND PARSE TO TOKENS STEP
        # Search for JADs in DB, download, verify and index

        agreement_type = "JAD"
        agreements_found = download_documents(date_range_start, date_range_end, agreement_type)
        # Validar si se guardaron todos o menos de los que encontrados
        # levantar error o warning
        logger.info(f"Downloaded {agreements_found} documents out of xx in the list")


        # ----- PARSE STEP
        # fetch from DB new JAD agreement_id List
        # Loop JADS

        

        # ------- FINAL VALIDATION AND CLOSE STEP
        # Determine overall success status based on individual step statuses
        overall_sync_ok = True
        # overall_sync_ok = (group_sync_status == 0 and 
        #                    user_sync_status == 0 and 
        #                    agreement_sync_status == 0)

        # UPDATE AND CLOSE DB SYNC TABLE
        # Calculate elapsed time
        end_time: datetime = utils.get_current_timestamp()
        hours, minutes, seconds = utils.calculate_elapsed_time(start_time, end_time)
        elapsed_str: str = utils.format_elapsed_time(hours, minutes, seconds)
        end_time_str: str = end_time.strftime('%Y-%m-%d %H:%M:%S')

        # Get final agreement count
        final_agreement_count = db.get_agreement_count()
        agreements_found = final_agreement_count - initial_agreement_count

        # Update SyncHistory with overall success status
        # log_file_path = "logs/test_log.log"
        log_lines = monitor.read_recent_log_lines(log_file_path)
        log_counts = monitor.count_log_records_by_level(log_lines)

        try:
            db.update_sync_history(
                lookup_run_id=sync_history_id,
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
        # _handle_failure(sync_history_id, initial_agreement_count, start_time, run_id)
        # Define Business decision to do next
        # fall back procedure
    except DatabaseError as e:
        logger.critical(f"Could not sync groups: {e}. Caused by: {e.original_exc} - exiting")
        return 1
    except APIError as e:
        logger.critical(f"Could not sync groups: {e}. Caused by: {e.original_exc} - exiting")
        # Define Business decision to do next
        # fall back procedure
    except AppError as e:
        logger.critical(f"Could not sync groups: {e}. - exiting")
        # Define Business decision to do next


    logger.debug(f"DEV_MAIN END")
    return 0

if __name__ == "__main__":
    exit_code: int = dev_main()
    logging.info(f"Logging Exit code: {exit_code}")
    print (f"exit code: {exit_code}")
    exit(exit_code)
