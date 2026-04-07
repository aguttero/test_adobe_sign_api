# LOGGER CONFIG
import logging

# SET LEVEL for each Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/test_log.log")
file_handler.setLevel(logging.DEBUG)

# SET GLOBAL Config
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
    handlers=[console_handler,file_handler]
)

# CREATE LOGGER OBJECT
logger = logging.getLogger(__name__)
## END LOGGER CONFIG

# IMPORT MODULES - AFTER LOGGER CONFIG
#import test_api as api
logger.debug("import test_database as db START")
import test_models as dbmodels
import test_database as db
logger.debug("import test_database as db END")
#from test_database import engine, Base 
# import test_models

# UPSERT LIST TO DB
# TEST DB OPS update user list
# user_list =[{'email': 'test2@email.com','first_name': 'Charlie','last_name': 'Update','status': 'test','sign_account_id': 'sample_user_id_02'}]

user_list_2 =[{'email': 'test2@email.com','first_name': 'Charlie','last_name': 'Update','status': 'test','id': 'sample_user_id_02'}]

# db.update_users(user_list)

# TEST DB OPS insert 1 user
new_user = {
    'email': 'test3@email.com',
    'first_name': 'Charlie_3', 
    'last_name': 'Test_3',
    'status': 'test',
    'adbe_sign_id': 'sample_user_id_03'
    }

## TEST CONFIG
SECRETS_FOLDER = "./client_secret/"
USER_LIST_FILENAME = f"{SECRETS_FOLDER}user_list.txt"
TEST_USER_LIST_FILENAME = f"{SECRETS_FOLDER}test_user_list.txt"


## RUN TEST CODE
print ("- - - - - -")
user_list = db.test_convert_txt_to_list(TEST_USER_LIST_FILENAME)

# print("Main: user_list:", user_list)
print ("- - - - - -")

# db.insert_users_session_add(new_user)
result = db.test_transform_user_list_keys(user_list)
print ("- - - - - -")
print("transformed_list: ", result)
print("transformed_list_len: ", len(result))
print ("- - - - - -")
db.test_bulk_insert_list(result)

# print ("select: ", db.select_user_by_email("test2@email.com"))
# db.update_user_status_by_email("test2@email.com", "updated")
# db.update_user_status_by_email_2("test3@email.com", "updated")
print ("- - - - - -")


# GET VALID TOKEN
# active_token = api.refresh_token()

# GET UPDATED USER LIST
# user_list = api.fetch_users(active_token)

logger.debug("End Main")