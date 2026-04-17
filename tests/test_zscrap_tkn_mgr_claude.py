# auth.py
import time
import logging
import httpx
from test_exceptions import AuthError

log = logging.getLogger(__name__)

AUTH_URL = "https://your-api.com/oauth/token"

def fetch_new_token(client_id, client_secret):
    """Calls the auth endpoint and returns raw token response."""
    try:
        response = httpx.post(
            AUTH_URL,
            data={
                "grant_type":    "client_credentials",
                "client_id":     client_id,
                "client_secret": client_secret,
            }
        )
        response.raise_for_status()
        return response.json()  # {"access_token": "...", "expires_in": 3600}

    except httpx.HTTPStatusError as e:
        raise AuthError(
            f"Token request failed — HTTP {e.response.status_code}",
            original_exc=e
        ) from e
    except httpx.RequestError as e:
        raise AuthError(
            "Token request failed — network error",
            original_exc=e
        ) from e


class TokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if self._is_expired():
            self._refresh()
        return self._token

    def _is_expired(self):
        return time.time() >= (self._expires_at - 60)

    def _refresh(self):
        log.info("Refreshing API access token")
        data = fetch_new_token(self.client_id, self.client_secret)
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]