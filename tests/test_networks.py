"""
Tests for network endpoints.
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
    with patch("handlers.networks.DynamoDBClient") as mock:
        yield mock


@pytest.fixture
def api_gateway_event():
    """Create a base API Gateway event."""
    return {
        "httpMethod": "GET",
        "path": "/api/v1/networks/N_HQ001/appliance/vlans",
        "headers": {
            "X-Cisco-Meraki-API-Key": "test-api-key-12345",
        },
        "queryStringParameters": None,
        "pathParameters": {"networkId": "N_HQ001"},
        "body": None,
    }


class TestGetNetworkVlans:
    """Tests for GET /networks/{networkId}/appliance/vlans endpoint."""

    def test_returns_vlans_successfully(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of VLANs."""
        mock_network = {"id": "N_HQ001", "name": "HQ-Network"}
        mock_vlans = [
            {"id": "10", "name": "Corporate", "subnet": "192.168.10.0/24"},
            {"id": "20", "name": "Guest", "subnet": "192.168.20.0/24"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_network
        mock_db_instance.get_entities_by_parent.return_value = mock_vlans

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2
        assert body[0]["name"] == "Corporate"

    def test_returns_404_for_nonexistent_network(self, mock_db_client, api_gateway_event):
        """Test 404 when network doesn't exist."""
        api_gateway_event["path"] = "/api/v1/networks/N_INVALID/appliance/vlans"
        api_gateway_event["pathParameters"] = {"networkId": "N_INVALID"}

        mock_db_client.return_value.get_entity.return_value = None

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 404


class TestGetNetworkClients:
    """Tests for GET /networks/{networkId}/clients endpoint."""

    def test_returns_clients_successfully(self, mock_db_client, api_gateway_event):
        """Test successful retrieval of network clients."""
        api_gateway_event["path"] = "/api/v1/networks/N_HQ001/clients"

        mock_network = {"id": "N_HQ001", "name": "HQ-Network"}
        mock_clients = [
            {"id": "k123456", "mac": "AC:DE:48:11:22:33", "ip": "192.168.10.100"},
            {"id": "k654321", "mac": "84:25:DB:44:55:66", "ip": "192.168.10.101"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_network
        mock_db_instance.get_entities_by_parent.return_value = mock_clients

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 2

    def test_respects_per_page_parameter(self, mock_db_client, api_gateway_event):
        """Test pagination with perPage parameter."""
        api_gateway_event["path"] = "/api/v1/networks/N_HQ001/clients"
        api_gateway_event["queryStringParameters"] = {"perPage": "1"}

        mock_network = {"id": "N_HQ001", "name": "HQ-Network"}
        mock_clients = [
            {"id": "k123456", "mac": "AC:DE:48:11:22:33"},
            {"id": "k654321", "mac": "84:25:DB:44:55:66"},
        ]

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.return_value = mock_network
        mock_db_instance.get_entities_by_parent.return_value = mock_clients

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body) == 1


class TestGetSiteToSiteVpn:
    """Tests for GET /networks/{networkId}/appliance/vpn/siteToSiteVpn endpoint."""

    def test_returns_vpn_config_for_hub(self, mock_db_client, api_gateway_event):
        """Test retrieval of hub VPN configuration."""
        api_gateway_event["path"] = "/api/v1/networks/N_HQ001/appliance/vpn/siteToSiteVpn"

        mock_network = {"id": "N_HQ001", "name": "HQ-Network"}
        mock_vpn_config = {
            "mode": "hub",
            "hubs": [],
            "subnets": [
                {"localSubnet": "192.168.10.0/24", "useVpn": True}
            ]
        }

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.side_effect = [mock_network, mock_vpn_config]

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["mode"] == "hub"

    def test_returns_vpn_config_for_spoke(self, mock_db_client, api_gateway_event):
        """Test retrieval of spoke VPN configuration."""
        api_gateway_event["path"] = "/api/v1/networks/N_BR001/appliance/vpn/siteToSiteVpn"
        api_gateway_event["pathParameters"] = {"networkId": "N_BR001"}

        mock_network = {"id": "N_BR001", "name": "Branch-A"}
        mock_vpn_config = {
            "mode": "spoke",
            "hubs": [{"hubId": "N_HQ001", "useDefaultRoute": True}],
            "subnets": [
                {"localSubnet": "192.168.100.0/24", "useVpn": True}
            ]
        }

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.side_effect = [mock_network, mock_vpn_config]

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["mode"] == "spoke"
        assert len(body["hubs"]) == 1

    def test_returns_default_config_when_vpn_not_configured(self, mock_db_client, api_gateway_event):
        """Test default response when no VPN is configured."""
        api_gateway_event["path"] = "/api/v1/networks/N_NOVPN/appliance/vpn/siteToSiteVpn"
        api_gateway_event["pathParameters"] = {"networkId": "N_NOVPN"}

        mock_network = {"id": "N_NOVPN", "name": "No-VPN-Network"}

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.side_effect = [mock_network, None]

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["mode"] == "none"


class TestGetCellularGatewaySubnetPool:
    """Tests for GET /networks/{networkId}/cellularGateway/subnetPool endpoint."""

    def test_returns_subnet_pool(self, mock_db_client, api_gateway_event):
        """Test retrieval of cellular gateway subnet pool."""
        api_gateway_event["path"] = "/api/v1/networks/N_BR001/cellularGateway/subnetPool"

        mock_network = {"id": "N_BR001", "name": "Branch-A"}
        mock_pool = {
            "deploymentMode": "routed",
            "cidr": "10.200.0.0",
            "mask": 16,
            "subnets": [
                {"serial": None, "name": "Subnet 1", "subnet": "10.200.1.0/24"}
            ]
        }

        mock_db_instance = mock_db_client.return_value
        mock_db_instance.get_entity.side_effect = [mock_network, mock_pool]

        response = lambda_handler(api_gateway_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["deploymentMode"] == "routed"
