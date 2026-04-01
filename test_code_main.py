import test_code_api as api
import test_code_db as dbmgr

active_token = api.refresh_token()

result = api.fetch_users(active_token)

