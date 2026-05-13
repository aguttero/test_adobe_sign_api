# old_api.py 0417am

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

def fetch_users() -> list[dict]:
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


def search_agreements_by_user(
    user_email: str,
    start_date: str,
    end_date: str,
    page_size: int = 100
) -> list[dict]:
    """
    Search agreements for a user using Adobe Sign /search endpoint.
    
    Args:
        user_email: Email of the user whose agreements to search.
        start_date: ISO format start date for createdDate filter (e.g., "2026-01-01T00:00:00Z").
        end_date: ISO format end date for createdDate filter (e.g., "2026-01-08T23:59:59Z").
        page_size: Number of results per page (default 100).
    
    Returns:
        List of agreement dictionaries matching criteria.
    """
    endpoint = SEARCH_ENDPOINT
    logger.info(f"Searching agreements for {user_email} from {start_date} to {end_date}")
    token = adbe_sign_token_manager.get_token()  # TokenManager handles auto-refresh
    
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
        'x-api-user': f'email:{user_email}',
        'x-ownership-scope': 'OWNED'
    }
    
    # Format end date to end of day
    end_date_formatted = end_date.replace("T00:00:00Z", "T23:59:59Z")
    
    payload = {
        "scope": ["AGREEMENT_ASSETS"],
        "agreementAssetsCriteria": {
            "type": ["AGREEMENT"],
            "createdDate": {
                "range": {
                    "min": start_date,
                    "max": end_date_formatted
                }
            },
            "startIndex": 0,
            "status": ["SIGNED"],
            "sortByField": "CREATED_DATE",
            "sortOrder": "ASC"
        }
    }
    
    all_agreements = []
    start_index = 0
    
    try:
        while True:
            # Update startIndex for pagination
            payload["agreementAssetsCriteria"]["startIndex"] = start_index
            
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("agreementAssetsResults", {}).get("agreementAssetsResultList", [])
            all_agreements.extend(results)
            
            # Check for more pages
            search_info = data.get("agreementAssetsResults", {}).get("searchPageInfo", {})
            next_index = search_info.get("nextIndex")
            
            if next_index is None:
                break
                
            start_index = next_index
            
        logger.info(f"Found {len(all_agreements)} agreements for user {user_email}")
        return all_agreements
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"API error for {user_email}: {e.response.status_code} - {e.response.text}")
        raise  # Re-raise to caller
    except Exception as e:
        logger.error(f"Unexpected error searching agreements for {user_email}: {e}")
        raise  # Re-raise to caller


def parse_adbe_date(date_str: str) -> Optional[datetime.date]:
    """Parse Adobe Sign date string to date object."""
    if not date_str:
        return None
    try:
        # Handle Z suffix
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.date()
    except ValueError as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def map_api_to_agreement(agreement_dict: dict, user_id: int) -> dict:
    """Map Adobe Sign API response to Agreement model fields."""
    created = parse_adbe_date(agreement_dict.get('createdDate', ''))
    modified = parse_adbe_date(agreement_dict.get('modifiedDate', ''))
    display = parse_adbe_date(agreement_dict.get('displayDate', agreement_dict.get('modifiedDate', '')))
    
    return {
        'agreement_id': agreement_dict.get('id'),
        'user_id': user_id,
        'display_date': display,
        'name': agreement_dict.get('name'),
        'type': agreement_dict.get('type', 'AGREEMENT'),
        'status': agreement_dict.get('status'),
        'workflow_id': agreement_dict.get('workflowId'),
        'group_id': agreement_dict.get('groupId'),
        'created_date': created,
        'last_event_date': modified,
    }