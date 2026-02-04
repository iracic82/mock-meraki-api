"""
Tests for device endpoints.
"""

import json
import os
import pytest
from unittest.mock import patch

# Set environment variables before importing app
os.environ["CONFIG_TABLE"] = "MerakiMock_Config_test"
os.environ["DATA_TABLE"] = "MerakiMock_Data_test"
os.environ["DEFAULT_TOPOLOGY"] = "hub_spoke"
os.environ["STRICT_AUTH"] = "false"

from app import lambda_handler


@pytest.fixture
def mock_db_client():
    """Create a mock DynamoDB client."""
    with patch("handlers.devices.DynamoDBClient") as mock:
        yield mock


@pytest.fixture
def api_gateway_event():
    """Create a base API Gateway event."""
    return {
        "httpMethod": "GET",
        "path": "/api/v1/devices/Q2AA-BBBB-CCCC/clients",
        "headers": {
            "X-Cisco-Meraki-API-Key": "test-api-key-12345",
        },
        "queryStringParameters": None,
        "pathParameters": {"serial": "Q2AA-BBBB-CCCC"},
        "body": None,
    }


class TestGetDeviceClients:
    """Tests for GET /devices/{serial}/clients endpoint."""

    def test_returns_clients_successfully(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of device clients."""
        mock_device = {
            "serial": "Q2AA-BBBB-CCCC",
            "model": "MS425-32",
            "name": "HQ-CORE-SW-01"
        }
        mock_clients = [
            {
                "id": "k123456",
                "mac": "AC:DE:48:11:22:33",
                "ip": "192.168.10.100",
                "description": "MACBOOK-A1B2",
                "manufacturer": "Apple",
                "vlan": "10",
                "usage": {"sent": 1000000, "recv": 5000000}
            },
            {
                "id": "k654321",
                "mac": "84:25:DB:44:55:66",
                "ip": "192.168.10.101",
                "description": "GALAXY-C3D4",
                "manufacturer": "Samsung",
                "vlan": "10",
                "usage": {"sent": 500000, "recv": 2000000}
            },
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_device
        mock_db_instance.get_entities_by_parent.return_value = mock_clients

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2
        assert body[0]["manufacturer"] == "Apple"
        assert body[1]["manufacturer"] == "Samsung"

    def test_returns_404_for_nonexistent_device(self, mock_db_client, api_gateway_event):
        """Test 404 when device doesn't exist."""
        api_gateway_event["path"] = "/api/v1/devices/INVALID-SERIAL/clients"
        api_gateway_event["pathParameters"] = {"serial": "INVALID-SERIAL"}

        mock_db_client.return_value.get_entity.return_value = None

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert "errors" in body

    def test_returns_empty_list_when_no_clients(self, mock_db_client, api_gateway_event):
        """Test empty response when device has no clients."""
        mock_device = {
            "serial": "Q2AA-BBBB-CCCC",
            "model": "MX450",
            "name": "HQ-MX-01"
        }

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_device
        mock_db_instance.get_entities_by_parent.return_value = []

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body == []

    def test_handles_timespan_parameter(self, mock_db_client, api_gateway_event):
        """Test that timespan parameter is accepted."""
        api_gateway_event["queryStringParameters"] = {"timespan": "86400"}

        mock_device = {"serial": "Q2AA-BBBB-CCCC", "model": "MS425-32"}
        mock_clients = [{"id": "k123456", "mac": "AC:DE:48:11:22:33"}]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_device
        mock_db_instance.get_entities_by_parent.return_value = mock_clients

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_returns_healthy(self):
        """Test that health check returns healthy status."""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {},
            "queryStringParameters": None,
            "pathParameters": None,
            "body": None,
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["service"] == "mock-meraki-api"

    def test_health_check_does_not_require_auth(self):
        """Test that health check doesn't require API key."""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {},  # No API key
            "queryStringParameters": None,
            "pathParameters": None,
            "body": None,
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 200
