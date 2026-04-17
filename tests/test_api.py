"""
Adobe Sign API client.
External HTTP calls only. Owns TokenManager internally.
"""
import logging
from typing import List, Optional

import requests
from dotenv import dotenv_values

from test_auth import TokenManager
from test_exceptions import APIError

# LOGGER CONFIG
logger = logging.getLogger(__name__)

# CREDENTIALS CONFIG
config = dotenv_values(".env")
CLIENT_ID: str = config.get("CLIENT_ID", "")
CLIENT_SECRET: str = config.get("CLIENT_SECRET", "")
REFRESH_TOKEN: str = config.get("REFRESH_TOKEN", "")

# API CONFIG
SHARD: str = config.get("ADOBE_SHARD","na1")
BASE_URL: str = f"https://api.{SHARD}.echosign.com"

# ENDPOINTS
FETCH_USER_LIST_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/users"


def get_token_manager() -> TokenManager:
    """Get the shared TokenManager instance (lazy initialization)."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    return _token_manager


# TokenManager instance (lazy initialization)
_token_manager: Optional[TokenManager] = None


def fetch_all_users() -> List[dict]:
    """Fetch all users from Adobe Sign API with pagination.
    
    Returns:
        List of user dictionaries from the API.
        
    Raises:
        APIError: If the API call fails.
    """
    all_users: List[dict] = []
    cursor: Optional[str] = None
    counter: int = 0
    token: str = get_token_manager().get_token()

    endpoint: str = FETCH_USER_LIST_ENDPOINT
    logger.info(f"Fetching users from {endpoint}")
    
    headers: dict = {
        'Authorization': f"Bearer {token}"
    }
    parameters: dict = {
        'cursor': None
    }

    try:
        while True:
            if cursor:
                parameters['cursor'] = cursor
               
            api_response = requests.get(endpoint, headers=headers, params=parameters)
            api_response.raise_for_status()
            
            response_data = api_response.json()
            all_users.extend(response_data['userInfoList'])
            
            cursor = response_data.get('page', {}).get('nextCursor')

            counter += 1
            logger.debug(f"counter: {counter}, cursor: {cursor}")
        
            if not cursor:
                logger.debug("No more cursor")
                break
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching users: {e.response.status_code} - {e.response.text}")
        raise APIError(f"Error fetching users: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code, original_exc=e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching users: {e}")
        raise APIError(f"Error fetching users: {e}", original_exc=e)

    logger.info(f"Fetched {len(all_users)} users")
    return all_users