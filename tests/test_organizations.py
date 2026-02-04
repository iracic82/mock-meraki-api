"""
Tests for organization endpoints.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

# Set environment variables before importing app
os.environ["CONFIG_TABLE"] = "MerakiMock_Config_test"
os.environ["DATA_TABLE"] = "MerakiMock_Data_test"
os.environ["DEFAULT_TOPOLOGY"] = "hub_spoke"
os.environ["STRICT_AUTH"] = "false"

from app import lambda_handler


@pytest.fixture
def mock_db_client():
    """Create a mock DynamoDB client."""
    with patch("handlers.organizations.DynamoDBClient") as mock:
        yield mock


@pytest.fixture
def api_gateway_event():
    """Create a base API Gateway event."""
    return {
        "httpMethod": "GET",
        "path": "/api/v1/organizations",
        "headers": {
            "X-Cisco-Meraki-API-Key": "test-api-key-12345",
        },
        "queryStringParameters": None,
        "pathParameters": None,
        "body": None,
    }


class TestGetOrganizations:
    """Tests for GET /organizations endpoint."""

    def test_returns_organizations_successfully(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of organizations."""
        mock_orgs = [
            {
                "id": "883652",
                "name": "Acme Corporation",
                "url": "https://mock.meraki.com/o/acme/manage/organization/overview",
                "api": {"enabled": True},
                "licensing": {"model": "co-term"},
            }
        ]
        mock_db_client.return_value.get_entities.return_value = mock_orgs

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 1
        assert body[0]["id"] == "883652"
        assert body[0]["name"] == "Acme Corporation"

    def test_returns_empty_list_when_no_organizations(self, mock_db_client, api_gateway_event):
        """Test empty response when no organizations exist."""
        mock_db_client.return_value.get_entities.return_value = []

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body == []

    def test_requires_api_key(self, api_gateway_event):
        """Test that missing API key returns 401."""
        api_gateway_event["headers"] = {}

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "errors" in body

    def test_uses_topology_from_header(self, mock_db_client, api_gateway_event):
        """Test that topology header is respected."""
        api_gateway_event["headers"]["X-Mock-Topology"] = "mesh"
        mock_db_client.return_value.get_entities.return_value = []

        lambda_handler(api_gateway_event, None)

        # Verify the correct topology was used
        mock_db_client.return_value.get_entities.assert_called_with("mesh", "organization")

    def test_uses_topology_from_query_param(self, mock_db_client, api_gateway_event):
        """Test that topology query parameter is respected."""
        api_gateway_event["queryStringParameters"] = {"topology": "multi_org"}
        mock_db_client.return_value.get_entities.return_value = []

        lambda_handler(api_gateway_event, None)

        mock_db_client.return_value.get_entities.assert_called_with("multi_org", "organization")


class TestGetOrganizationNetworks:
    """Tests for GET /organizations/{organizationId}/networks endpoint."""

    def test_returns_networks_for_organization(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of networks."""
        api_gateway_event["path"] = "/api/v1/organizations/883652/networks"
        api_gateway_event["pathParameters"] = {"organizationId": "883652"}

        mock_org = {"id": "883652", "name": "Acme Corporation"}
        mock_networks = [
            {"id": "N_HQ001", "organizationId": "883652", "name": "HQ-Network"},
            {"id": "N_BR001", "organizationId": "883652", "name": "Branch-A"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_org
        mock_db_instance.get_entities_by_parent.return_value = mock_networks

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2

    def test_returns_404_for_nonexistent_organization(self, mock_db_client, api_gateway_event):
        """Test 404 when organization doesn't exist."""
        api_gateway_event["path"] = "/api/v1/organizations/999999/networks"
        api_gateway_event["pathParameters"] = {"organizationId": "999999"}

        mock_db_client.return_value.get_entity.return_value = None

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 404


class TestGetOrganizationDevices:
    """Tests for GET /organizations/{organizationId}/devices endpoint."""

    def test_returns_devices_for_organization(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of devices."""
        api_gateway_event["path"] = "/api/v1/organizations/883652/devices"
        api_gateway_event["pathParameters"] = {"organizationId": "883652"}

        mock_org = {"id": "883652", "name": "Acme Corporation"}
        mock_devices = [
            {"serial": "Q2AA-BBBB-CCCC", "model": "MX450", "name": "HQ-MX-01"},
            {"serial": "Q2DD-EEEE-FFFF", "model": "MS425-32", "name": "HQ-SW-01"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_org
        mock_db_instance.get_entities_by_parent.return_value = mock_devices

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2
        assert body[0]["serial"] == "Q2AA-BBBB-CCCC"


class TestGetOrganizationDevicesAvailabilities:
    """Tests for GET /organizations/{organizationId}/devices/availabilities endpoint."""

    def test_returns_device_availabilities(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of device availabilities."""
        api_gateway_event["path"] = "/api/v1/organizations/883652/devices/availabilities"
        api_gateway_event["pathParameters"] = {"organizationId": "883652"}

        mock_org = {"id": "883652", "name": "Acme Corporation"}
        mock_availabilities = [
            {"serial": "Q2AA-BBBB-CCCC", "status": "online"},
            {"serial": "Q2DD-EEEE-FFFF", "status": "alerting"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_org
        mock_db_instance.get_entities_by_parent.return_value = mock_availabilities

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2
        assert body[0]["status"] == "online"
