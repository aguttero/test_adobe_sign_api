"""
Token management for Adobe Sign API.
Handles OAuth token fetching, storage, expiration tracking, and refresh logic.
No business logic.
"""
import logging
import time
from dotenv import dotenv_values
import requests
from typing import Optional, Tuple

from test_exceptions import AuthError

logger = logging.getLogger(__name__)

# CONFIG - Credentials from environment variables
config = dotenv_values(".env")
SHARD = config.get("ADOBE_SHARD", "na1")
BASE_URL = f"https://api.{SHARD}.echosign.com"
REFRESH_ENDPOINT = f"{BASE_URL}/oauth/v2/refresh"

TOKEN_BUFFER_SECONDS = 300


def _refresh_token(client_id: str, client_secret: str, refresh_token: str) -> Tuple[str, int]:
    """Internal refresh function.

    Args:
        client_id: Adobe Sign OAuth client ID.
        client_secret: Adobe Sign OAuth client secret.
        refresh_token: Current refresh token.

    Returns:
        Tuple of (new_access_token, expiration_period).

    Raises:
        AuthError: If token refresh fails.
    """
    import os
    logger.debug("Refreshing token from Adobe Sign API")    

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
            raise AuthError(error_msg)

        logger.info("Token refreshed successfully")
        return new_access_token, expiration_period

    except requests.exceptions.HTTPError as e:
        error_msg = f"Token refresh failed: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        raise AuthError(error_msg, original_exc=e)
    except requests.exceptions.RequestException as e:
        error_msg = f"Token refresh failed: {e}"
        logger.error(error_msg)
        raise AuthError(error_msg, original_exc=e)


class TokenManager:
    """Manages OAuth token with automatic refresh and expiration tracking."""

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """Initialize token manager.

        Args:
            client_id: Adobe Sign OAuth client ID.
            client_secret: Adobe Sign OAuth client secret.
            refresh_token: Current refresh token.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token string.

        Raises:
            AuthError: If token refresh fails.
        """
        if self._is_expired():
            self._refresh()
        return self._token
    
    def _is_expired(self) -> bool:
        """Check if token is expired or will expire within buffer time."""
        return time.time() >= (self._expires_at - TOKEN_BUFFER_SECONDS)
    
    def _refresh(self) -> None:
        """Refresh the access token."""
        logger.info("Refreshing API access token")
        token_data = _refresh_token(self.client_id, self.client_secret, self.refresh_token)
        self._token = token_data[0]
        self._expires_at = time.time() + token_data[1]

