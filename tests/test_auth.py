"""
Unit tests for the TokenManager class in src/auth.py.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time
import requests

from auth import TokenManager, _refresh_token

class TestTokenManager(unittest.TestCase):

    def setUp(self):
        # Mocking dotenv_values and requests.post for all tests
        # Adjust patch target to reflect the new location of the code being tested
        self.mock_dotenv_values = patch('src.auth.dotenv_values', return_value={
            'CLIENT_ID': 'mock_client_id',
            'CLIENT_SECRET': 'mock_client_secret',
            'REFRESH_TOKEN': 'mock_refresh_token',
            'ADOBE_SHARD': 'mock_shard'
        }).start()
        self.mock_requests_post = patch('src.auth.requests.post').start()
        self.mock_logging = patch('src.auth.logger').start()
        
        self.token_manager = TokenManager('mock_client_id', 'mock_client_secret', 'mock_refresh_token')
        # Ensure token is not initially set, simulating a first call
        self.token_manager._token = None
        self.token_manager._expires_at = 0

    def tearDown(self):
        patch.stopall()

    def test_get_token_initial(self):
        """Test getting token for the first time, should trigger refresh."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status.return_value = None
        self.mock_requests_post.return_value = mock_response

        token = self.token_manager.get_token()
        self.assertEqual(token, 'new_access_token')
        self.mock_requests_post.assert_called_once()
        self.mock_logging.info.assert_any_call("Refreshing API access token")

    def test_get_token_valid(self):
        """Test getting token when it's still valid."""
        # Simulate a token that is already acquired and valid
        self.token_manager._token = 'valid_access_token'
        self.token_manager._expires_at = time.time() + 7200 # Expires in 2 hours

        token = self.token_manager.get_token()
        self.assertEqual(token, 'valid_access_token')
        self.mock_requests_post.assert_not_called() # Should not refresh

    def test_get_token_needs_refresh(self):
        """Test getting token when it's expired or near expiration."""
        # Simulate token expiring soon (within buffer)
        self.token_manager._token = 'old_access_token'
        self.token_manager._expires_at = time.time() + 150 # Expires in 2.5 minutes (less than 300s buffer)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'refreshed_access_token',
            'expires_in': 3600
        }
        mock_response.raise_for_status.return_value = None
        self.mock_requests_post.return_value = mock_response

        token = self.token_manager.get_token()
        self.assertEqual(token, 'refreshed_access_token')
        self.mock_requests_post.assert_called_once()
        self.mock_logging.info.assert_any_call("Refreshing API access token")

    def test_refresh_token_success(self):
        """Test the internal _refresh method success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'successful_refresh_token',
            'expires_in': 7200
        }
        mock_response.raise_for_status.return_value = None
        self.mock_requests_post.return_value = mock_response

        self.token_manager._refresh()
        self.assertEqual(self.token_manager._token, 'successful_refresh_token')
        self.assertGreater(self.token_manager._expires_at, time.time())
        self.mock_logging.info.assert_any_call("Token refreshed successfully")

    def test_refresh_token_http_error(self):
        """Test _refresh method raises APIError on HTTPError."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error: Bad Request for url: ...", response=mock_response)
        self.mock_requests_post.return_value = mock_response

        with self.assertRaisesRegex(APIError, "Token refresh failed: 400 - Bad Request"):
            self.token_manager._refresh()
        self.mock_logging.error.assert_any_call("Token refresh failed: 400 - Bad Request")

    def test_refresh_token_request_exception(self):
        """Test _refresh method raises APIError on general RequestException."""
        self.mock_requests_post.side_effect = requests.exceptions.RequestException("Network Error")

        with self.assertRaisesRegex(APIError, "Token refresh failed: Network Error"):
            self.token_manager._refresh()
        self.mock_logging.error.assert_any_call("Token refresh failed: Network Error")

    def test_refresh_token_no_access_token(self):
        """Test _refresh method raises APIError if no access_token in response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'refresh_token': 'something_else'} # Missing access_token
        mock_response.raise_for_status.return_value = None
        self.mock_requests_post.return_value = mock_response

        with self.assertRaisesRegex(APIError, "Token refresh failed: no access_token in response"):
            self.token_manager._refresh()
        self.mock_logging.error.assert_any_call("Token refresh failed: no access_token in response")

    def test_is_expired_true(self):
        """Test _is_expired returns True when token is expired or near expiry."""
        # Simulate token expiring very soon
        self.token_manager._expires_at = time.time() + 100 # Expires in 100 seconds
        self.assertTrue(self.token_manager._is_expired())

        # Simulate token expired long ago
        self.token_manager._expires_at = time.time() - 3600 # Expired an hour ago
        self.assertTrue(self.token_manager._is_expired())

    def test_is_expired_false(self):
        """Test _is_expired returns False when token is valid."""
        # Simulate token expiring in the future, beyond the buffer
        self.token_manager._expires_at = time.time() + 7200 # Expires in 2 hours
        self.assertFalse(self.token_manager._is_expired())

if __name__ == '__main__':
    unittest.main()
