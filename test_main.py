# LOGGER CONFIG
import logging

# SET LEVEL for each Handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("logs/test_log.log")
file_handler.setLevel(logging.INFO)

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
import test_logger as mod
#import test_api as api
import test_database as db


# UPSERT LIST TO DB
# TEST DB OPS update user list
user_list =[]
db.update_users(user_list)

# TEST DB OPS insert 1 user
new_user = {
    'email': 'test@email.com',
    'first_name': 'Charlie', 
    'last_name': 'Test',
    'status': 'test',
    'sign_user_id': 'sample_user_id_01'
    }

db.try_insert(new_user)

# GET VALID TOKEN
# active_token = api.refresh_token()

# GET UPDATED USER LIST
# user_list = api.fetch_users(active_token)

logger.error("Error Main")