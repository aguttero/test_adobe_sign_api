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
SEARCH_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/search"


# Valid participant roles for signers
SIGNER_ROLES: set = {"SIGNER", "APPROVER"}

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


def search_agreements(
    user_email: str,
    user_adbe_sign_id: str,
    date_range_start: str,
    date_range_end: str
) -> List[dict]:
    """Search agreements for a given user within a date range.

    Args:
        user_email: Email address of the agreement owner.
        user_adbe_sign_id: Adobe Sign user ID of the agreement owner.
        date_range_start: Start date for search (ISO format).
        date_range_end: End date for search (ISO format).

    Returns:
        List of agreement dictionaries with signers.

    Raises:
        APIError: If the API call fails.
    """
    all_agreements: List[dict] = []
    next_index: Optional[int] = None
    page_counter: int = 0

    token: str = get_token_manager().get_token()
    endpoint: str = SEARCH_ENDPOINT
    logger.info(f"Searching agreements for {user_email} from {date_range_start} to {date_range_end}")

    headers: dict = {
        'Authorization': f"Bearer {token}",
        'x-ownership-scope': 'OWNED',
        'x-api-user': f'email:{user_email}'
    }

    payload: dict = {
        "query": "*",
        "filterRules": [
            {
                "field": "ROLES",
                "operator": "EQUALS",
                "values": ["SENDER"]
            },
            {
                "field": "CREATION_DATE",
                "operator": "AFTER",
                "values": [date_range_start]
            },
            {
                "field": "CREATION_DATE",
                "operator": "BEFORE",
                "values": [date_range_end]
            }
        ],
        "pagination": {
            "pageSize": 100
        }
    }

    try:
        while True:
            if next_index is not None:
                payload["pagination"]["startCursor"] = next_index

            api_response = requests.post(endpoint, headers=headers, json=payload)
            api_response.raise_for_status()

            response_data = api_response.json()
            page_counter += 1
            logger.debug(f"Page {page_counter}, status: {api_response.status_code}")

            # Parse agreements from response
            agreements_results = response_data.get("agreementAssetsResults", {})
            agreement_list = agreements_results.get("agreementAssetsResultList", [])
            total_hits = agreements_results.get("totalHits", 0)

            for agreement in agreement_list:
                # Extract signers (SIGNER or APPROVER roles)
                signers: List[dict] = []
                participant_list = agreement.get("participantList", [])
                for participant in participant_list:
                    roles = participant.get("role", [])
                    # Check if participant has SIGNER or APPROVER role
                    if any(role in SIGNER_ROLES for role in roles):
                        signers.append({
                            "signer_email": participant.get("email", ""),
                            "signer_full_name": participant.get("fullName", ""),
                            "signer_role": roles[0] if roles else ""
                        })

                # Parse dates
                created_date_str = agreement.get("createdDate", "")
                modified_date_str = agreement.get("modifiedDate", "")

                transformed = {
                    "email": user_email,
                    "adbe_sign_id": user_adbe_sign_id,
                    "group_id": agreement.get("groupId", ""),
                    "signers": signers,
                    "created_date": created_date_str,
                    "last_event_date": modified_date_str,
                    "name": agreement.get("name", ""),
                    "agreement_id": agreement.get("id", ""),
                    "workflow_id": agreement.get("workflowId", ""),
                    "status": agreement.get("status", "")
                }
                all_agreements.append(transformed)

            # Check for next page
            page_info = agreements_results.get("searchPageInfo", {})
            next_index = page_info.get("nextIndex")

            if next_index is None:
                logger.debug("No more pages")
                break

    except requests.exceptions.HTTPError as e:
        logger.error(f"Error searching agreements: {e.response.status_code} - {e.response.text}")
        raise APIError(f"Error searching agreements: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code, original_exc=e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching agreements: {e}")
        raise APIError(f"Error searching agreements: {e}", original_exc=e)

    logger.info(f"Found {len(all_agreements)} agreements for {user_email}")
    return all_agreements