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
import test_database as db
logger.debug("import test_database as db END")
#from test_database import engine, Base 
# import test_models

# UPSERT LIST TO DB
# TEST DB OPS update user list
user_list =[{'email': 'test@email.com','first_name': 'Charlie','last_name': 'Update','status': 'test','sign_user_id': 'updated_user_id_01'}]

# db.update_users(user_list)

# TEST DB OPS insert 1 user
new_user = {
    'email': 'test3@email.com',
    'first_name': 'Charlie_3', 
    'last_name': 'Test_3',
    'status': 'test',
    'sign_user_id': 'sample_user_id_03'
    }


print ("- - - - - -")
# db.insert_users(new_user)
# print ("select: ", db.select_user_by_email("test2@email.com"))
db.update_user_status_by_email("test2@email.com", "updated")
db.update_user_status_by_email_2("test3@email.com", "updated")
print ("- - - - - -")


# GET VALID TOKEN
# active_token = api.refresh_token()

# GET UPDATED USER LIST
# user_list = api.fetch_users(active_token)

logger.debug("End Main")