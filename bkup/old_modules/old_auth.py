# old_test_auth.py 0417am

import logging
import re
import time
import requests
from typing import Optional


logger = logging.getLogger(__name__)

# CONFIG

SHARD = "na1"
BASE_URL = f"https://api.{SHARD}.echosign.com"
REFRESH_ENDPOINT = f"{BASE_URL}/oauth/v2/refresh"

SECRETS_FOLDER = "./client_secret/"
TOKEN_FILENAME = f"{SECRETS_FOLDER}adbe_dev_token.txt"
TOKEN_BUFFER_SECONDS = 300

def _refresh_token(client_id, client_secret, refresh_token):
    """Internal refresh function.

        Returns:
            New access token string.

        Raises:
            RuntimeError: If token refresh fails.
        """
    logger.info("Refreshing token from Adobe Sign API")    

    payload = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
    }

    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        api_response = requests.post(REFRESH_ENDPOINT, data=payload, headers=headers)
        api_response.raise_for_status()

        tokens = api_response.json()
        new_access_token = tokens.get("access_token")
        expiration_period = tokens.get("expires_in")

        if not new_access_token:
            error_msg = "Token refresh failed: no access_token in response"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

         # Write token to file for other test modules
        with open(TOKEN_FILENAME, "w") as f:
            f.write(new_access_token)

        logger.info("Token refreshed and saved successfully")
        return new_access_token, expiration_period

    except requests.exceptions.HTTPError as e:
        error_msg = f"Token refresh failed: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Token refresh failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


class TokenManager:
    """Manages OAuth token with automatic refresh and expiration tracking."""

    # def __init__(self, token: str, expires_in: int = 3600):
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """Initialize token manager.

        Args:
            refresh_token: Access token string.
            expires_in: Token lifetime in seconds (default 1 hour).
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if self._is_expired():
            self._refresh()
        return self._token
    
    def _is_expired(self):
        return time.time() >= (self._expires_at - TOKEN_BUFFER_SECONDS)
    
    def _refresh(self):
        logger.info("Refreshing API access token")
        data = _refresh_token(self.client_id, self.client_secret, self.refresh_token)
        self._token = data[0]
        self._expires_at = time.time() + data[1]


    # @property
    # def token(self) -> str:
    #     """Get token, refreshing if expired."""
    #     if self._is_expired:
    #         self._do_refresh()
    #     return self._token

    # @property
    # def _is_expired(self) -> bool:
    #     """Check if token is expired."""
    #     elapsed = time.time() - self._created_at
    #     is_expired = elapsed >= self._expires_in
    #     if is_expired:
    #         logger.debug(f"Token expired: {elapsed}s elapsed >= {self._expires_in}s")
    #     return is_expired

    # @property
    # def is_valid(self) -> bool:
    #     """Check if token is still valid (not expired)."""
    #     return not self._is_expired

    # def _do_refresh(self) -> None:
    #     """Refresh the token."""
    #     logger.info("Token expired, refreshing...")
    #     new_token = _refresh_token()
    #     self._token = new_token
    #     self._created_at = time.time()
    #     self._expires_in = 3600
    #     logger.info("Token refreshed successfully")

# Init Token Manager:
# _token_manager: Optional["TokenManager"] = TokenManager("empty_token",0)
# sign_token_manager = TokenManager(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)


def old_refresh_token() -> str:
    """Internal refresh function.

    Returns:
        New access token string.

    Raises:
        RuntimeError: If token refresh fails.
    """
    logger.info("Refreshing token from Adobe Sign API")

    payload = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        api_response = requests.post(REFRESH_ENDPOINT, data=payload, headers=headers)
        api_response.raise_for_status()

        tokens = api_response.json()
        new_access_token = tokens.get("access_token")

        if not new_access_token:
            error_msg = "Token refresh failed: no access_token in response"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Write token to file for other test modules
        with open(TOKEN_FILENAME, "w") as f:
            f.write(new_access_token)

        logger.info("Token refreshed and saved successfully")
        return new_access_token

    except requests.exceptions.HTTPError as e:
        error_msg = f"Token refresh failed: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Token refresh failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def old_init_token_manager() -> "TokenManager":
    """Initialize module-level TokenManager with a fresh token.

    Returns:
        TokenManager instance with freshly fetched access token.

    Raises:
        RuntimeError: If token refresh fails.
    """
    global _token_manager
    logger.info("Initializing TokenManager with fresh token")
    _token_manager = TokenManager(_refresh_token())
    return _token_manager


def old_get_token() -> str:
    """Get valid token, raises RuntimeError if error gettting token

    Returns:
        Valid access token string.

    Raises:
        RuntimeError: If token refresh fails.
    """
    if _token_manager.is_valid:
        return _token_manager.token
    else:
        logger.error("TokenManager API error")
        raise RuntimeError("TokenManager API error")


def old_get_token_manager() -> Optional["TokenManager"]:
    """Get the TokenManager instance.

    Returns:
        TokenManager instance or None if not initialized.
    """
    return _token_manager