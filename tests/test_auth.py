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

