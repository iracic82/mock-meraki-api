"""
Network-level endpoint handlers for Mock Meraki API.

Handles:
- GET /networks/{networkId}/appliance/vlans
- GET /networks/{networkId}/clients
- GET /networks/{networkId}/vlanProfiles
- GET /networks/{networkId}/cellularGateway/subnetPool
- GET /networks/{networkId}/appliance/vpn/siteToSiteVpn
"""

import json
import logging
from typing import Any

from db.dynamodb import (
    DynamoDBClient,
    ENTITY_NETWORK,
    ENTITY_VLAN,
    ENTITY_VLAN_PROFILE,
    ENTITY_NETWORK_CLIENT,
    ENTITY_VPN_CONFIG,
    ENTITY_CELLULAR_SUBNET_POOL,
)

logger = logging.getLogger(__name__)


def _response(status_code: int, body: Any) -> dict:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body) if body is not None else "",
    }


def get_network_vlans(topology: str, network_id: str) -> dict:
    """
    Get all VLANs configured on a network's appliance.

    Args:
        topology: Active topology name
        network_id: Network ID

    Returns:
        API Gateway response with list of VLANs
    """
    logger.info(f"Getting VLANs for network {network_id}")

    db = DynamoDBClient()

    # Verify network exists
    network = db.get_entity(topology, ENTITY_NETWORK, network_id)
    if not network:
        return _response(404, {"errors": [f"Network {network_id} not found"]})

    # Get VLANs by parent network
    vlans = db.get_entities_by_parent(
        topology, ENTITY_NETWORK, network_id, ENTITY_VLAN
    )

    logger.info(f"Returning {len(vlans)} VLANs")
    return _response(200, vlans)


def get_network_vlan_profiles(topology: str, network_id: str) -> dict:
    """
    Get VLAN profiles for a network.

    Args:
        topology: Active topology name
        network_id: Network ID

    Returns:
        API Gateway response with list of VLAN profiles
    """
    logger.info(f"Getting VLAN profiles for network {network_id}")

    db = DynamoDBClient()

    # Verify network exists
    network = db.get_entity(topology, ENTITY_NETWORK, network_id)
    if not network:
        return _response(404, {"errors": [f"Network {network_id} not found"]})

    # Get VLAN profiles by parent network
    profiles = db.get_entities_by_parent(
        topology, ENTITY_NETWORK, network_id, ENTITY_VLAN_PROFILE
    )

    logger.info(f"Returning {len(profiles)} VLAN profiles")
    return _response(200, profiles)


def get_network_clients(topology: str, network_id: str, query_params: dict) -> dict:
    """
    Get clients connected to a network.

    Args:
        topology: Active topology name
        network_id: Network ID
        query_params: Query parameters (timespan, perPage, etc.)

    Returns:
        API Gateway response with list of clients
    """
    logger.info(f"Getting clients for network {network_id}")

    db = DynamoDBClient()

    # Verify network exists
    network = db.get_entity(topology, ENTITY_NETWORK, network_id)
    if not network:
        return _response(404, {"errors": [f"Network {network_id} not found"]})

    # Get clients by parent network
    clients = db.get_entities_by_parent(
        topology, ENTITY_NETWORK, network_id, ENTITY_NETWORK_CLIENT
    )

    # Apply pagination if requested
    per_page = int(query_params.get("perPage", 1000))
    starting_after = query_params.get("startingAfter")

    if starting_after:
        # Find the index of the starting point
        start_idx = 0
        for i, client in enumerate(clients):
            if client.get("id") == starting_after:
                start_idx = i + 1
                break
        clients = clients[start_idx:start_idx + per_page]
    else:
        clients = clients[:per_page]

    logger.info(f"Returning {len(clients)} clients")
    return _response(200, clients)


def get_cellular_gateway_subnet_pool(topology: str, network_id: str) -> dict:
    """
    Get cellular gateway subnet pool for a network.

    Args:
        topology: Active topology name
        network_id: Network ID

    Returns:
        API Gateway response with subnet pool configuration
    """
    logger.info(f"Getting cellular gateway subnet pool for network {network_id}")

    db = DynamoDBClient()

    # Verify network exists
    network = db.get_entity(topology, ENTITY_NETWORK, network_id)
    if not network:
        return _response(404, {"errors": [f"Network {network_id} not found"]})

    # Get subnet pool - there should be only one per network
    subnet_pool = db.get_entity(topology, ENTITY_CELLULAR_SUBNET_POOL, network_id)

    if not subnet_pool:
        # Return empty/default response if no cellular gateway
        return _response(200, {
            "deploymentMode": "passthrough",
            "cidr": "",
            "mask": 0,
            "subnets": []
        })

    return _response(200, subnet_pool)


def get_site_to_site_vpn(topology: str, network_id: str) -> dict:
    """
    Get site-to-site VPN configuration for a network.

    Args:
        topology: Active topology name
        network_id: Network ID

    Returns:
        API Gateway response with VPN configuration
    """
    logger.info(f"Getting site-to-site VPN config for network {network_id}")

    db = DynamoDBClient()

    # Verify network exists
    network = db.get_entity(topology, ENTITY_NETWORK, network_id)
    if not network:
        return _response(404, {"errors": [f"Network {network_id} not found"]})

    # Get VPN config - there should be only one per network
    vpn_config = db.get_entity(topology, ENTITY_VPN_CONFIG, network_id)

    if not vpn_config:
        # Return default response if no VPN configured
        return _response(200, {
            "mode": "none",
            "hubs": [],
            "subnets": []
        })

    return _response(200, vpn_config)
