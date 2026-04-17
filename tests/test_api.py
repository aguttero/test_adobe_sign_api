import logging
from datetime import datetime
import requests
from test_auth import TokenManager
from dotenv import dotenv_values
from typing import Optional


# LOGGER CONFIG
logger = logging.getLogger(__name__)

# CREDENTIALS CONFIG
config = dotenv_values(".env")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
REFRESH_TOKEN = config.get("REFRESH_TOKEN")

# API CONFIG
SHARD = "na1"
BASE_URL = f"https://api.{SHARD}.echosign.com"

## ENDPOINTS
GET_URI_ENDPOINT = f"https://api.{SHARD}.adobesign.com/api/rest/v6/baseUris"
FETCH_USER_LIST_ENDPOINT = f"{BASE_URL}/api/rest/v6/users"
SEARCH_ENDPOINT = f"{BASE_URL}/api/rest/v6/search"
SECRETS_FOLDER = "./client_secret/"

# TEST CONFIG
USER_LIST_FILENAME = f"{SECRETS_FOLDER}user_list.txt"


# Init Token Manager Instance for Adobe Sign
adbe_sign_token_manager = TokenManager(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)


def get_uris() -> Optional[str]:
    """Get Adobe Sign base URIs."""
    endpoint = GET_URI_ENDPOINT
    logger.info(f"Fetching URIs from {endpoint}")
    token = adbe_sign_token_manager.get_token()  # TokenManager handles auto-refresh

    headers = {
            'Authorization': f"Bearer {token}"
        }

    try:
        api_response = requests.get(endpoint, headers=headers)
        api_response.raise_for_status()
        
        uris = api_response.json()
        api_base_uri = uris.get("apiAccessPoint")
        logger.info(f"Retrieved URIs: {api_base_uri}")
        return api_base_uri
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching URIs: {e.response.status_code} - {e.response.text}")
        raise  # Re-raise to caller


def test_fetch_token():
    """ Test function to test _token_manager"""
    token = adbe_sign_token_manager.get_token()
    print("OK GET TOKEN: ", token)

def fetch_all_users() -> list[dict]:
    """Fetch all users from Adobe Sign API with pagination."""
    all_users = []
    cursor = None
    counter = 0
    token = adbe_sign_token_manager.get_token()  # TokenManager handles auto-refresh

    endpoint = FETCH_USER_LIST_ENDPOINT
    logger.info(f"Fetching users from {endpoint}")
    
    headers = {
            'Authorization': f"Bearer {token}"
        }
    parameters = {
        'cursor': None
        }

    try:
        while True:
            if cursor:
                parameters['cursor'] = cursor
               
            api_response = requests.get(endpoint, headers=headers, params=parameters)
            api_response.raise_for_status()
            
            # This extends the current page results to all_users list
            response_data = api_response.json()
            all_users.extend(response_data['userInfoList'])
            
            # Look for next cursor index
            cursor = response_data.get('page',{}).get('nextCursor')

            counter +=1
            logger.debug(f"counter: {counter}")
            logger.debug (f"cursor: {cursor}")
        
            if not cursor:
                logger.debug(f"No more cursor")
                break
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching users: {e.response.status_code} - {e.response.text}")
        raise  # Re-raise to caller

    logger.info(f"Fetched {len(all_users)} users")
    return all_users
