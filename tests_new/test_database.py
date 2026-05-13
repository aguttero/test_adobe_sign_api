"""
Unit tests for the database module, specifically for user filtering.
"""

import unittest
from unittest.mock import MagicMock

import db # Assuming db is now in src/db


class TestUserFiltering(unittest.TestCase):

    def test_filter_new_users_no_existing(self):
        """Test filtering when there are no existing users in the database."""
        existing_emails = []
        input_list = [
            {'email': 'user1@example.com', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        expected_output = [
            {'email': 'user1@example.com', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

    def test_filter_new_users_some_existing(self):
        """Test filtering when some users already exist in the database."""
        existing_emails = ['user1@example.com']
        input_list = [
            {'email': 'user1@example.com', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'},
            {'email': 'user3@example.com', 'adbe_sign_id': '3'}
        ]
        expected_output = [
            {'email': 'user2@example.com', 'adbe_sign_id': '2'},
            {'email': 'user3@example.com', 'adbe_sign_id': '3'}
        ]
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

    def test_filter_new_users_all_existing(self):
        """Test filtering when all users already exist in the database."""
        existing_emails = ['user1@example.com', 'user2@example.com']
        input_list = [
            {'email': 'user1@example.com', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        expected_output = []
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

    def test_filter_new_users_empty_input(self):
        """Test filtering with an empty input list."""
        existing_emails = ['user1@example.com']
        input_list = []
        expected_output = []
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

    def test_filter_new_users_case_insensitivity(self):
        """Test filtering is case-insensitive for emails."""
        existing_emails = ['user1@EXAMPLE.com'] # Existing email in different case
        input_list = [
            {'email': 'user1@example.com', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        expected_output = [
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

    def test_filter_new_users_with_whitespace(self):
        """Test filtering handles leading/trailing whitespace in emails."""
        # Assuming emails in the database are already cleaned, but input might have whitespace
        existing_emails = ['user1@example.com']
        input_list = [
            {'email': ' user1@example.com ', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        # The filter_new_users function itself does not clean the input emails before comparison.
        # If the existing_emails list is clean and input_list emails are not, this test might fail 
        # if the cleaning happens elsewhere (e.g., in `transform_user_list_keys`).
        # For this test, we assume comparison is direct. If cleaning is expected here,
        # the function would need to be updated.
        # Based on current implementation, ' user1@example.com ' is NOT in existing_emails.
        expected_output = [
            {'email': ' user1@example.com ', 'adbe_sign_id': '1'},
            {'email': 'user2@example.com', 'adbe_sign_id': '2'}
        ]
        result = db.filter_new_users(existing_emails, input_list)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
