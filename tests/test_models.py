"""
Unit tests for the data models, focusing on agreement parsing.
"""

import unittest
from unittest.mock import MagicMock
from datetime import date

import models  # Assuming models are now in src/models
from exceptions import DatabaseError


class TestAgreementParsing(unittest.TestCase):

    def setUp(self):
        # Mocking convert_to_sqlite_date and logger for the tests
        # Adjust patch target to reflect the new location of the code being tested
        self.mock_convert_date = unittest.mock.patch('src.models.convert_to_sqlite_date', return_value=date(2023, 1, 1)).start()
        self.mock_logger = unittest.mock.patch('src.models.logger').start()

    def tearDown(self):
        unittest.mock.patch.stopall()

    def test_parse_agreements_success(self):
        """Test parsing a valid list of agreements."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "name": "Agreement One",
                "status": "SIGNED",
                "workflowId": "wf1_id",
                "groupId": "groupA_id",
                "userId": "user1_id",
                "createdDate": "2023-01-10T10:00:00Z",
                "modifiedDate": "2023-01-15T12:00:00Z",
                "docFieldList": [
                    {"subType": "signer1", "defaultValue": "Signer One Name"},
                    {"subType": "role1", "defaultValue": "SIGNER"}
                ]
            },
            {
                "id": "agreement2_id",
                "name": "Agreement Two",
                "status": "SENT",
                "workflowId": "wf2_id",
                "groupId": "groupB_id",
                "userId": "user2_id",
                "createdDate": "2023-01-11T11:00:00Z",
                "modifiedDate": "2023-01-16T13:00:00Z",
                "docFieldList": [
                    {"subType": "signer1", "defaultValue": "Signer Two Name"},
                    {"subType": "role1", "defaultValue": "SIGNER"},
                    {"subType": "signer2", "defaultValue": "Another Signer"},
                    {"subType": "role2", "defaultValue": "APPROVER"}
                ]
            }
        ]
        # Mocking the group_pk_lookup to provide valid group IDs
        group_pk_lookup = {
            "groupA_id": 10,
            "groupB_id": 20
        }

        parsed_agreements = models.parse_agreements(mock_api_data, group_pk_lookup)

        self.assertEqual(len(parsed_agreements), 2)

        # Asserting the first agreement
        self.assertIsInstance(parsed_agreements[0], models.Agreement)
        self.assertEqual(parsed_agreements[0].agreement_id, "agreement1_id")
        self.assertEqual(parsed_agreements[0].name, "Agreement One")
        self.assertEqual(parsed_agreements[0].status, "SIGNED")
        self.assertEqual(parsed_agreements[0].workflow_id, "wf1_id")
        self.assertEqual(parsed_agreements[0].group_id, "groupA_id")
        self.assertEqual(parsed_agreements[0].group_id_ref, 10) # Should be the internal PK
        self.assertEqual(parsed_agreements[0].created_date, date(2023, 1, 1))
        self.assertEqual(parsed_agreements[0].modified_date, date(2023, 1, 1))
        self.assertEqual(parsed_agreements[0].user_id, "user1_id")
        self.assertEqual(len(parsed_agreements[0].doc_field_contents), 2)
        self.assertEqual(parsed_agreements[0].doc_field_contents[0].agreement_subtype, "signer1")
        self.assertEqual(parsed_agreements[0].doc_field_contents[0].requester_area, "Signer One Name")
        self.assertEqual(parsed_agreements[0].doc_field_contents[1].agreement_subtype, "role1")
        self.assertEqual(parsed_agreements[0].doc_field_contents[1].requester_area, "SIGNER")

        # Asserting the second agreement
        self.assertIsInstance(parsed_agreements[1], models.Agreement)
        self.assertEqual(parsed_agreements[1].agreement_id, "agreement2_id")
        self.assertEqual(parsed_agreements[1].name, "Agreement Two")
        self.assertEqual(parsed_agreements[1].status, "SENT")
        self.assertEqual(parsed_agreements[1].workflow_id, "wf2_id")
        self.assertEqual(parsed_agreements[1].group_id, "groupB_id")
        self.assertEqual(parsed_agreements[1].group_id_ref, 20)
        self.assertEqual(parsed_agreements[1].created_date, date(2023, 1, 1))
        self.assertEqual(parsed_agreements[1].modified_date, date(2023, 1, 1))
        self.assertEqual(parsed_agreements[1].user_id, "user2_id")
        self.assertEqual(len(parsed_agreements[1].doc_field_contents), 4)
        self.assertEqual(parsed_agreements[1].doc_field_contents[0].agreement_subtype, "signer1")
        self.assertEqual(parsed_agreements[1].doc_field_contents[0].requester_area, "Signer Two Name")

        self.mock_convert_date.assert_any_call("2023-01-10T10:00:00Z")
        self.mock_convert_date.assert_any_call("2023-01-15T12:00:00Z")
        self.mock_convert_date.assert_any_call("2023-01-11T11:00:00Z")
        self.mock_convert_date.assert_any_call("2023-01-16T13:00:00Z")
        self.mock_logger.warning.assert_not_called() # No warnings expected

    def test_parse_agreements_missing_group_id(self):
        """Test parsing when an agreement has an unknown groupId."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "name": "Agreement One",
                "status": "SIGNED",
                "workflowId": "wf1_id",
                "groupId": "unknown_group_id", # This groupId is not in our lookup
                "userId": "user1_id",
                "createdDate": "2023-01-10T10:00:00Z",
                "modifiedDate": "2023-01-15T12:00:00Z"
            }
        ]
        group_pk_lookup = {
            "groupA_id": 10
        }

        parsed_agreements = models.parse_agreements(mock_api_data, group_pk_lookup)

        self.assertEqual(len(parsed_agreements), 0) # Should skip this agreement
        self.mock_logger.warning.assert_called_once_with("Skipping agreement agreement1_id — unknown adobe_group_id")

    def test_parse_agreements_empty_input(self):
        """Test parsing with an empty API data list."""
        mock_api_data = []
        group_pk_lookup = {
            "groupA_id": 10
        }

        parsed_agreements = models.parse_agreements(mock_api_data, group_pk_lookup)

        self.assertEqual(len(parsed_agreements), 0)
        self.mock_logger.debug.assert_called_once_with("Parsed 0 agreements")

    def test_parse_agreements_missing_fields(self):
        """Test parsing when some expected fields are missing in API data."""
        mock_api_data = [
            {
                # Missing id, name, status, workflowId, userId
                "groupId": "groupA_id",
                "createdDate": "2023-01-10T10:00:00Z",
                "modifiedDate": "2023-01-15T12:00:00Z",
                "docFieldList": [
                    {"subType": "signer1", "defaultValue": "Signer One Name"}
                ]
            }
        ]
        group_pk_lookup = {
            "groupA_id": 10
        }

        parsed_agreements = models.parse_agreements(mock_api_data, group_pk_lookup)

        self.assertEqual(len(parsed_agreements), 1)
        # Check that missing fields are handled gracefully (e.g., None or default values)
        self.assertIsInstance(parsed_agreements[0], models.Agreement)
        self.assertIsNone(parsed_agreements[0].agreement_id)
        self.assertIsNone(parsed_agreements[0].name)
        self.assertIsNone(parsed_agreements[0].status)
        self.assertIsNone(parsed_agreements[0].workflow_id)
        self.assertEqual(parsed_agreements[0].group_id, "groupA_id")
        self.assertEqual(parsed_agreements[0].group_id_ref, 10)
        self.assertEqual(parsed_agreements[0].created_date, date(2023, 1, 1))
        self.assertEqual(parsed_agreements[0].modified_date, date(2023, 1, 1))
        self.assertIsNone(parsed_agreements[0].user_id)
        self.assertEqual(len(parsed_agreements[0].doc_field_contents), 1)
        self.assertEqual(parsed_agreements[0].doc_field_contents[0].agreement_subtype, "signer1")
        self.assertEqual(parsed_agreements[0].doc_field_contents[0].requester_area, "Signer One Name")

    # --- Tests for parse_agreement_signers --- 

    def test_parse_agreement_signers_success(self):
        """Test parsing signers from a typical agreement structure."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "participantList": [
                    {
                        "email": "signer1@example.com",
                        "fullName": "Signer One",
                        "role": ["SIGNER"],
                        "order": 1
                    },
                    {
                        "email": "approver@example.com",
                        "fullName": "Approver",
                        "role": ["APPROVER"],
                        "order": 2
                    }
                ]
            },
            {
                "id": "agreement2_id",
                "participantList": [
                    {
                        "email": "signer2@example.com",
                        "fullName": "Signer Two",
                        "role": ["SIGNER"],
                        "order": 1
                    }
                ]
            }
        ]

        parsed_signers = models.parse_agreement_signers(mock_api_data)

        self.assertEqual(len(parsed_signers), 3)

        # Asserting the first signer
        self.assertIsInstance(parsed_signers[0], models.AgreementSigner)
        self.assertEqual(parsed_signers[0].agreement_id, "agreement1_id")
        self.assertEqual(parsed_signers[0].signer_email, "signer1@example.com")
        self.assertEqual(parsed_signers[0].signer_full_name, "Signer One")
        self.assertEqual(parsed_signers[0].signer_role, "SIGNER")
        self.assertEqual(parsed_signers[0].signer_order, 1)

        # Asserting the second signer (approver)
        self.assertIsInstance(parsed_signers[1], models.AgreementSigner)
        self.assertEqual(parsed_signers[1].agreement_id, "agreement1_id")
        self.assertEqual(parsed_signers[1].signer_email, "approver@example.com")
        self.assertEqual(parsed_signers[1].signer_full_name, "Approver")
        self.assertEqual(parsed_signers[1].signer_role, "APPROVER")
        self.assertEqual(parsed_signers[1].signer_order, 2)

        # Asserting the third signer
        self.assertIsInstance(parsed_signers[2], models.AgreementSigner)
        self.assertEqual(parsed_signers[2].agreement_id, "agreement2_id")
        self.assertEqual(parsed_signers[2].signer_email, "signer2@example.com")
        self.assertEqual(parsed_signers[2].signer_full_name, "Signer Two")
        self.assertEqual(parsed_signers[2].signer_role, "SIGNER")
        self.assertEqual(parsed_signers[2].signer_order, None)

    def test_parse_agreement_signers_no_participants(self):
        """Test parsing when an agreement has no participantList."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "participantList": [] # Empty participant list
            }
        ]

        parsed_signers = models.parse_agreement_signers(mock_api_data)
        self.assertEqual(len(parsed_signers), 0)
        self.mock_logger.warning.assert_not_called()

    def test_parse_agreement_signers_malformed_signer(self):
        """Test parsing with a malformed signer (missing email)."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "participantList": [
                    {
                        "fullName": "Signer One",
                        "role": ["SIGNER"],
                        "order": 1
                    } # Missing email
                ]
            }
        ]

        parsed_signers = models.parse_agreement_signers(mock_api_data)
        self.assertEqual(len(parsed_signers), 0) # Malformed signer should be skipped
        self.mock_logger.warning.assert_called_once_with("Skipping malformed signer in agreement agreement1_id")

    def test_parse_agreement_signers_multiple_roles(self):
        """Test parsing when a signer has multiple roles (should take the first)."""
        mock_api_data = [
            {
                "id": "agreement1_id",
                "participantList": [
                    {
                        "email": "signer@example.com",
                        "fullName": "Signer",
                        "role": ["SIGNER", "APPROVER"], # Multiple roles
                        "order": 1
                    }
                ]
            }
        ]

        parsed_signers = models.parse_agreement_signers(mock_api_data)
        self.assertEqual(len(parsed_signers), 1)
        self.assertEqual(parsed_signers[0].signer_role, "SIGNER") # Should take the first role

    def test_parse_agreement_signers_empty_api_data(self):
        """Test parsing with empty API data list."""
        mock_api_data = []
        parsed_signers = models.parse_agreement_signers(mock_api_data)
        self.assertEqual(len(parsed_signers), 0)
        self.mock_logger.debug.assert_called_once_with("Parsed 0 signers across 0 agreements")

if __name__ == '__main__':
    unittest.main()
