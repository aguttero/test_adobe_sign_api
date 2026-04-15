# LOGGER GLOBAL CONFIG
import logging
from datetime import datetime, timedelta

# SET LEVEL for each Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# file_handler = logging.FileHandler("logs/test_log.log")
file_handler = logging.FileHandler("tests/logs/test_log.log")
file_handler.setLevel(logging.DEBUG)

# SET GLOBAL Config
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(module)s:%(funcName)s - %(message)s',
    handlers=[console_handler,file_handler]
)

# CREATE LOGGER OBJECT
logger = logging.getLogger(__name__)
## END LOGGER CONFIG

# IMPORT MODULES - AFTER LOGGER CONFIG
logger.debug("import test_database as db START")
#import tests.test_models as dbmodels
import test_models as dbmodels
import test_database as db
logger.debug("import test_database as db END")


## DB HEALTH VALIDATION
# TODO implement DB closed ok check at the end of main
db_health_ok = db.check_db_last_closed_status()
if not db_health_ok:
    # TODO Define DB Recovery Action
    pass

## DEFINE RANGE DATE TO SEARCH
# Search range is 7 days. From Sunday 00 UTC to Sunday 00 UTC
# Search runs Sunday 05AM UTC
# TODO GET LAST RANGE END DATE
last_end_date_str = "2026-03-01T00:00:00Z" # Read this date_str from DB Exec Log
new_start_range_date_str = last_end_date_str
new_range_end_date = datetime.fromisoformat(last_end_date_str) + timedelta(days=7)
new_range_end_date_str = f"{new_range_end_date.date()}T00:00:00Z"

# VALIDATE search range is in the past
datetime_today = datetime.today()
naive_new_end_range_date = datetime.fromisoformat(new_range_end_date_str.replace("T00:00:00Z"," 00:00:00"))
print ("- - - - ")
if datetime_today >= naive_new_end_range_date:
    print (f"OK to run search. Naive range end datetime: {naive_new_end_range_date}")
    logger.debug(f"OK Range end date in the past. Naive range end datetime: {naive_new_end_range_date}")
else:
    print ("ERROR - Reschedule Chron")
    logger.critical(f"RUM DATE ERROR: Search Range NOT in the PAST - CHECK MAIN RUN CHRON. Naive range end datetime > dateime.now(): {naive_new_end_range_date}")



# UPSERT LIST TO DB
# TEST DB OPS update user list
# user_list =[{'email': 'test2@email.com','first_name': 'Charlie','last_name': 'Update','status': 'test','sign_account_id': 'sample_user_id_02'}]

## TEST DATA
# user_list_2 =[{'email': 'test2@email.com','first_name': 'Charlie','last_name': 'Update','status': 'test','id': 'sample_user_id_02'}]
# db.update_users(user_list)

## TEST CONFIG
SECRETS_FOLDER = "client_secret/"
USER_LIST_FILENAME = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME = f"{SECRETS_FOLDER}test_user_list.txt"


## RUN TEST CODE
print ("- - - - - -")
# LOAD user_list FROM FILE
user_list = db.test_convert_txt_to_list(TEST_USER_LIST_FILENAME)
print ("- - - - - -")


# TRANSFORM user_list DICT KEY names to match Table 
transformed_user_list = db.test_transform_user_list_keys(user_list)
print("transformed_list_len: ", len(transformed_user_list))

#### -> INSERT NEW USERS by email KEY
# test_user_list = []
db.insert_new_items_by_email_key(transformed_user_list)


# print ("select: ", db.select_user_by_email("test2@email.com"))
# db.update_user_status_by_email("test2@email.com", "updated")
# db.update_user_status_by_email_2("test3@email.com", "updated")
print ("- - - - - -")


# GET VALID TOKEN
# active_token = api.refresh_token()

# GET UPDATED USER LIST
# user_list = api.fetch_users(active_token)

logger.debug("End Main")