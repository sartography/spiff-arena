import unittest

from main import is_sensitive_field_name
from main import redacted


class RedactionTest(unittest.TestCase):
    def test_redacts_sensitive_field_name_patterns(self):
        payload = {
            "clientSecret": "client-secret-value",
            "refresh-token": "refresh-token-value",
            "X-Api-Key": "api-key-value",
            "awsAccessKeyId": "aws-access-key-value",
            "private_key": "private-key-value",
            "basic_auth_username": "username-value",
            "headers": {
                "Authorization": "Bearer token-value",
                "X-Amz-Security-Token": "security-token-value",
                "Accept": "application/json",
            },
            "ordinary": "visible",
        }

        assert redacted(payload) == {
            "clientSecret": "***REDACTED***",
            "refresh-token": "***REDACTED***",
            "X-Api-Key": "***REDACTED***",
            "awsAccessKeyId": "***REDACTED***",
            "private_key": "***REDACTED***",
            "basic_auth_username": "***REDACTED***",
            "headers": {
                "Authorization": "***REDACTED***",
                "X-Amz-Security-Token": "***REDACTED***",
                "Accept": "application/json",
            },
            "ordinary": "visible",
        }

    def test_redacts_value_fields_with_sensitive_descriptors(self):
        payload = {
            "parameters": [
                {"id": "api_key", "type": "str", "value": "api-key-value"},
                {"name": "clientSecret", "type": "str", "value": "client-secret-value"},
                {"field_name": "display_name", "type": "str", "value": "visible"},
                {"type": "password", "value": "password-value"},
            ],
        }

        assert redacted(payload) == {
            "parameters": [
                {"id": "api_key", "type": "str", "value": "***REDACTED***"},
                {"name": "clientSecret", "type": "str", "value": "***REDACTED***"},
                {"field_name": "display_name", "type": "str", "value": "visible"},
                {"type": "password", "value": "***REDACTED***"},
            ],
        }

    def test_sensitive_field_name_patterns_are_delimiter_and_case_tolerant(self):
        sensitive_field_names = [
            "apiKey",
            "api-key",
            "api_key",
            "refreshToken",
            "client.secret",
            "X-Auth-Token",
            "jwt",
        ]

        assert all(is_sensitive_field_name(field_name) for field_name in sensitive_field_names)
        assert not is_sensitive_field_name("display_name")


if __name__ == "__main__":
    unittest.main()
