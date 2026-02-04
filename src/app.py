"""
Mock Meraki Dashboard API - Main Lambda Handler

Routes incoming API Gateway requests to appropriate handlers based on path and method.
Supports topology switching via header or query parameter.
"""

import json
import logging
import os
import re
from typing import Any

from middleware.auth import validate_api_key
from handlers import organizations, networks, devices, admin

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Main Lambda handler for all API requests.

    Routes requests based on HTTP method and path to appropriate handlers.
    Extracts topology from header or query parameter.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Extract request details
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "")
        headers = event.get("headers") or {}
        query_params = event.get("queryStringParameters") or {}
        path_params = event.get("pathParameters") or {}
        body = event.get("body")

        # Normalize headers to lowercase keys
        headers = {k.lower(): v for k, v in headers.items()}

        # Health check - no auth required
        if path == "/health":
            return _response(200, {"status": "healthy", "service": "mock-meraki-api"})

        # Admin endpoints - no Meraki auth required
        if path.startswith("/admin"):
            return _route_admin(http_method, path, path_params, query_params, body, headers)

        # Validate Meraki API key for all other endpoints
        auth_result = validate_api_key(headers)
        if not auth_result["valid"]:
            return _response(401, {"errors": [auth_result["error"]]})

        # Extract topology selection
        topology = _get_topology(headers, query_params)

        # Route to appropriate handler
        return _route_request(http_method, path, path_params, query_params, topology)

    except Exception as e:
        logger.exception(f"Unhandled error: {str(e)}")
        return _response(500, {"errors": [f"Internal server error: {str(e)}"]})


def _get_topology(headers: dict, query_params: dict) -> str:
    """Extract topology from header or query parameter, with fallback to default."""
    # Priority: header > query param > environment default
    topology = headers.get("x-mock-topology")
    if not topology:
        topology = query_params.get("topology")
    if not topology:
        topology = os.environ.get("DEFAULT_TOPOLOGY", "hub_spoke")
    return topology


def _route_request(method: str, path: str, path_params: dict, query_params: dict, topology: str) -> dict:
    """Route API v1 requests to appropriate handlers."""

    # Organization endpoints
    if path == "/api/v1/organizations":
        return organizations.get_organizations(topology)

    org_networks_match = re.match(r"/api/v1/organizations/([^/]+)/networks", path)
    if org_networks_match:
        org_id = path_params.get("organizationId") or org_networks_match.group(1)
        return organizations.get_organization_networks(topology, org_id)

    org_devices_avail_match = re.match(r"/api/v1/organizations/([^/]+)/devices/availabilities", path)
    if org_devices_avail_match:
        org_id = path_params.get("organizationId") or org_devices_avail_match.group(1)
        return organizations.get_organization_devices_availabilities(topology, org_id)

    org_devices_match = re.match(r"/api/v1/organizations/([^/]+)/devices", path)
    if org_devices_match:
        org_id = path_params.get("organizationId") or org_devices_match.group(1)
        return organizations.get_organization_devices(topology, org_id)

    # Network endpoints
    net_vlans_match = re.match(r"/api/v1/networks/([^/]+)/appliance/vlans", path)
    if net_vlans_match:
        net_id = path_params.get("networkId") or net_vlans_match.group(1)
        return networks.get_network_vlans(topology, net_id)

    net_vlan_profiles_match = re.match(r"/api/v1/networks/([^/]+)/vlanProfiles", path)
    if net_vlan_profiles_match:
        net_id = path_params.get("networkId") or net_vlan_profiles_match.group(1)
        return networks.get_network_vlan_profiles(topology, net_id)

    net_clients_match = re.match(r"/api/v1/networks/([^/]+)/clients", path)
    if net_clients_match:
        net_id = path_params.get("networkId") or net_clients_match.group(1)
        return networks.get_network_clients(topology, net_id, query_params)

    net_cellular_match = re.match(r"/api/v1/networks/([^/]+)/cellularGateway/subnetPool", path)
    if net_cellular_match:
        net_id = path_params.get("networkId") or net_cellular_match.group(1)
        return networks.get_cellular_gateway_subnet_pool(topology, net_id)

    net_vpn_match = re.match(r"/api/v1/networks/([^/]+)/appliance/vpn/siteToSiteVpn", path)
    if net_vpn_match:
        net_id = path_params.get("networkId") or net_vpn_match.group(1)
        return networks.get_site_to_site_vpn(topology, net_id)

    # Device endpoints
    device_clients_match = re.match(r"/api/v1/devices/([^/]+)/clients", path)
    if device_clients_match:
        serial = path_params.get("serial") or device_clients_match.group(1)
        return devices.get_device_clients(topology, serial, query_params)

    # Not found
    return _response(404, {"errors": [f"Endpoint not found: {path}"]})


def _route_admin(method: str, path: str, path_params: dict, query_params: dict, body: str, headers: dict) -> dict:
    """Route admin endpoints for topology management."""

    if path == "/admin/topologies" and method == "GET":
        return admin.list_topologies()

    if path == "/admin/topology/active" and method == "GET":
        return admin.get_active_topology()

    topology_activate_match = re.match(r"/admin/topology/([^/]+)/activate", path)
    if topology_activate_match and method == "PUT":
        topology_name = path_params.get("name") or topology_activate_match.group(1)
        return admin.activate_topology(topology_name)

    if path == "/admin/topology" and method == "POST":
        return admin.create_topology(body)

    return _response(404, {"errors": [f"Admin endpoint not found: {path}"]})


def _response(status_code: int, body: Any) -> dict:
    """Create API Gateway response with proper headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Cisco-Meraki-API-Key,X-Mock-Topology",
        },
        "body": json.dumps(body) if body else "",
    }
