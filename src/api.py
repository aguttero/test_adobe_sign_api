"""
Adobe Sign API client.
External HTTP calls only. Owns TokenManager internally.
"""
import logging
from typing import List, Optional

import requests
from dotenv import dotenv_values

from auth import TokenManager
from exceptions import APIError


# LOGGER CONFIG
logger = logging.getLogger(__name__)

# CREDENTIALS CONFIG
config = dotenv_values(".env")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
REFRESH_TOKEN = config.get("REFRESH_TOKEN")

# VALIDATE THAT CREDENTIALS LOADED OK
logger.debug(f"DOT ENV LOAD VALIDATION")
if not CLIENT_ID:
    logger.critical(f"Failed to load API credentials from .env")
    raise APIError(f"Failed to load API credentials from .env")

# API CONFIG
SHARD = config.get("ADOBE_SHARD")
BASE_URL = f"https://api.{SHARD}.echosign.com"

# ENDPOINTS
FETCH_USER_LIST_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/users"
FETCH_GROUPS_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/groups"
SEARCH_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/search"
FETCH_WORKFLOWS_ENDPOINT: str = f"{BASE_URL}/api/rest/v6/workflows"


# Valid participant roles for signers (includes FORM_FILLER)
SIGNER_ROLES: set = {"SIGNER", "APPROVER", "FORM_FILLER"}

def get_token_manager() -> TokenManager:
    """Get the shared TokenManager instance (lazy initialization)."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
        # logger.debug(f"_token_manager.client_id: {_token_manager.client_id}, {_token_manager.client_secret}, {_token_manager.refresh_token}, _token={_token_manager._token}")
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


def fetch_all_groups() -> List[dict]:
    """Fetch all groups from Adobe Sign API.

    Returns:
        List of group dictionaries from the API.

    Raises:
        APIError: If the API call fails.
    """
    all_groups: List[dict] = []
    cursor: Optional[str] = None
    counter: int = 0
    token: str = get_token_manager().get_token()

    endpoint: str = FETCH_GROUPS_ENDPOINT
    logger.debug(f"Fetching groups from {endpoint}")

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
            all_groups.extend(response_data.get('groupInfoList', []))

            cursor = response_data.get('page', {}).get('nextCursor')

            counter += 1
            logger.debug(f"counter: {counter}, cursor: {cursor}")

            if not cursor:
                logger.debug("No more cursor")
                break

    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching groups: {e.response.status_code} - {e.response.text}")
        raise APIError(f"Error fetching groups: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code, original_exc=e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching groups: {e}")
        raise APIError(f"Error fetching groups: {e}", original_exc=e)

    logger.debug(f"Fetched {len(all_groups)} groups")
    return all_groups

def fetch_all_workflows() -> List[dict]:
    """Fetch all workflows from Adobe Sign API.
    
    Returns:
        List of workflow dictionaries from the API.
        
    Raises:
        APIError: If the API call fails.
    """
    all_workflows: List[dict] = []
    cursor: Optional[str] = None
    token: str = get_token_manager().get_token()

    endpoint: str = FETCH_WORKFLOWS_ENDPOINT
    logger.info(f"Fetching workflows from {endpoint}")

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
            all_workflows.extend(response_data.get('userWorkflowList', []))

            cursor = response_data.get('pageInfo', {}).get('nextCursor')

            if not cursor:
                logger.debug("No more cursor for workflows")
                break

    except requests.exceptions.HTTPError as e:
        logger.error(f"Error fetching workflows: {e.response.status_code} - {e.response.text}")
        raise APIError(f"Error fetching workflows: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code, original_exc=e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching workflows: {e}")
        raise APIError(f"Error fetching workflows: {e}", original_exc=e)

    logger.info(f"Fetched {len(all_workflows)} workflows")
    return all_workflows

def search_agreements_user(
    user_email: str,
    date_range_start: str,
    date_range_end: str
) -> List[dict]:
    """Search agreements for a given user within a date range and persist to DB.

    Args:
        user_email: Email address of the agreement owner.
        date_range_start: Start date for search (ISO format).
        date_range_end: End date for search (ISO format).

    Returns:
        List of agreement dictionaries.

    Raises:
        APIError: If the API call fails.
    """
    all_agreements: List[dict] = []
    next_index: Optional[int] = None
    page_counter: int = 0

    token: str = get_token_manager().get_token()
    endpoint: str = SEARCH_ENDPOINT
    logger.debug(f"Searching agreements for {user_email} from {date_range_start} to {date_range_end}")

    headers: dict = {
        'Authorization': f"Bearer {token}",
        'x-api-user': f'email:{user_email}'
    }

    payload: dict = {
            "scope": ["AGREEMENT_ASSETS"],
            "agreementAssetsCriteria": {
                "role": ["SENDER"],
                "type": ["AGREEMENT"],
                "createdDate": {
                    "range": {
                        "min": date_range_start,
                        "max": date_range_end
                    }
                },
                "startIndex": 0,
                "pageSize": 100,
                "status": ["SIGNED"],
                "sortByField": "CREATED_DATE",
                "sortOrder": "ASC"
            }
        }

    try:
        while True:
            if next_index is not None:
                payload["agreementAssetsCriteria"]["startIndex"] = next_index

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
                # Extract signers (SIGNER, APPROVER, or FORM_FILLER roles)
                signers: List[dict] = []
                participant_list = agreement.get("participantList", [])

                # Handle case when owner is also a signer/form filler (no participantList returned)
                # This happens when agreement has SENDER + SIGNER or SENDER + FORM_FILLER roles
                owner_roles = agreement.get("role", [])
                is_owner_also_signer = "SIGNER" in owner_roles and "SENDER" in owner_roles
                is_owner_also_form_filler = "FORM_FILLER" in owner_roles and "SENDER" in owner_roles

                if is_owner_also_signer and not participant_list:
                    # Owner is also a signer - add them as a signer manually
                    logger.debug(f"Owner {user_email} is also a signer for agreement {agreement.get('id')}")
                    signers.append({
                        "signer_email": user_email,
                        "signer_full_name": "",  # Owner full name not in response
                        "signer_role": "SIGNER"
                    })
                elif is_owner_also_form_filler and not participant_list:
                    # Owner is also a form filler - add them as a signer manually
                    logger.debug(f"Owner {user_email} is also a form filler for agreement {agreement.get('id')}")
                    signers.append({
                        "signer_email": user_email,
                        "signer_full_name": "",  # Owner full name not in response
                        "signer_role": "FORM_FILLER"
                    })
                else:
                    # Normal case - extract signers from participantList
                    for participant in participant_list:
                        roles = participant.get("role", [])
                        # Check if participant has SIGNER, APPROVER, or FORM_FILLER role
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
                    "adbe_sign_id": agreement.get("userId"),
                    "group_id": agreement.get("groupId"),  # API groupId
                    "signers": signers,
                    "created_date": created_date_str,
                    "modified_date": modified_date_str,
                    "name": agreement.get("name", ""),
                    "agreement_id": agreement.get("id"),
                    "workflow_id": agreement.get("workflowId", ""),
                    "status": agreement.get("status")
                }
                all_agreements.append(transformed)

            # Check for next page
            page_info = agreements_results.get("searchPageInfo", {})
            next_index = page_info.get("nextIndex")
            # logger.debug(f"next_index value: {next_index!r} - data type {type(next_index)}")

            if next_index is None:
                logger.debug("No more pages")
                break

    except requests.exceptions.HTTPError as e:
        logger.error(f"Error searching agreements: {e.response.status_code} - {e.response.text}")
        
        # Check for INVALID_USER error (401)
        error_text = e.response.text
        if "INVALID_USER" in error_text:
            logger.warning(f"User {user_email} is invalid (INVALID_USER)")
            raise APIError(f"Invalid user: {user_email}", status_code=e.response.status_code, original_exc=e)
        
        raise APIError(f"Error searching agreements: {e.response.status_code} - {e.response.text}", status_code=e.response.status_code, original_exc=e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching agreements: {e}")
        raise APIError(f"Error searching agreements: {e}", original_exc=e)

    logger.debug(f"Found {len(all_agreements)} agreements for {user_email}")
    return all_agreements
