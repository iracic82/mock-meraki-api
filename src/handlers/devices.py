"""
Device-level endpoint handlers for Mock Meraki API.

Handles:
- GET /devices/{serial}/clients
- GET /devices/{serial}/appliance/dhcp/subnets
"""

import json
import logging
from typing import Any

from db.dynamodb import (
    DynamoDBClient,
    ENTITY_DEVICE,
    ENTITY_CLIENT,
    ENTITY_VLAN,
    ENTITY_NETWORK_CLIENT,
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


def get_device_clients(topology: str, serial: str, query_params: dict) -> dict:
    """
    Get clients connected to a specific device.

    Args:
        topology: Active topology name
        serial: Device serial number
        query_params: Query parameters (timespan, etc.)

    Returns:
        API Gateway response with list of clients
    """
    logger.info(f"Getting clients for device {serial}")

    db = DynamoDBClient()

    # Verify device exists
    device = db.get_entity(topology, ENTITY_DEVICE, serial)
    if not device:
        return _response(404, {"errors": [f"Device {serial} not found"]})

    # Get clients by parent device
    clients = db.get_entities_by_parent(
        topology, ENTITY_DEVICE, serial, ENTITY_CLIENT
    )

    # Apply timespan filter if provided (mock implementation)
    timespan = query_params.get("timespan")
    if timespan:
        # In real implementation, filter by lastSeen timestamp
        # For mock, we return all clients
        pass

    logger.info(f"Returning {len(clients)} clients for device {serial}")
    return _response(200, clients)


def get_device_appliance_dhcp_subnets(topology: str, serial: str) -> dict:
    """
    Get DHCP subnet information for an MX appliance.

    Returns subnet utilization stats per VLAN - how many IPs are used vs free.

    Args:
        topology: Active topology name
        serial: Device serial number (must be an MX appliance)

    Returns:
        API Gateway response with list of DHCP subnet stats
    """
    logger.info(f"Getting DHCP subnets for device {serial}")

    db = DynamoDBClient()

    # Get device and verify it exists
    device = db.get_entity(topology, ENTITY_DEVICE, serial)
    if not device:
        return _response(404, {"errors": [f"Device {serial} not found"]})

    # Verify device is an appliance (MX)
    product_type = device.get("productType", "")
    if product_type != "appliance":
        return _response(400, {"errors": [f"Device {serial} is not an appliance (type: {product_type})"]})

    # Get network ID from device
    network_id = device.get("networkId")
    if not network_id:
        return _response(400, {"errors": [f"Device {serial} has no network assignment"]})

    # Get VLANs for this network
    vlans = db.get_entities_by_parent(topology, "network", network_id, ENTITY_VLAN)
    if not vlans:
        return _response(200, [])

    # Get all network clients to count per VLAN
    clients = db.get_entities_by_parent(topology, "network", network_id, ENTITY_NETWORK_CLIENT)

    # Count clients per VLAN
    clients_per_vlan = {}
    for client in clients:
        vlan_id = client.get("vlan")
        if vlan_id:
            # Convert to int for comparison
            try:
                vlan_id_int = int(vlan_id)
                clients_per_vlan[vlan_id_int] = clients_per_vlan.get(vlan_id_int, 0) + 1
            except (ValueError, TypeError):
                pass

    # Build DHCP subnet response
    dhcp_subnets = []
    for vlan in vlans:
        vlan_id = vlan.get("id")
        subnet = vlan.get("subnet")

        if not subnet:
            continue

        # Convert vlan_id to int
        try:
            vlan_id_int = int(vlan_id) if vlan_id else 0
        except (ValueError, TypeError):
            vlan_id_int = 0

        # Calculate subnet size from CIDR
        # e.g., /24 = 256 addresses, minus network, broadcast, gateway = 253 usable
        usable_ips = _calculate_usable_ips(subnet)
        used_count = clients_per_vlan.get(vlan_id_int, 0)
        free_count = max(0, usable_ips - used_count)

        dhcp_subnets.append({
            "subnet": subnet,
            "vlanId": vlan_id_int,
            "usedCount": used_count,
            "freeCount": free_count
        })

    logger.info(f"Returning {len(dhcp_subnets)} DHCP subnets for device {serial}")
    return _response(200, dhcp_subnets)


def _calculate_usable_ips(subnet: str) -> int:
    """
    Calculate number of usable IPs in a subnet.

    Args:
        subnet: CIDR notation (e.g., "192.168.10.0/24")

    Returns:
        Number of usable IPs (total - network - broadcast - gateway)
    """
    try:
        if "/" not in subnet:
            return 253  # Default to /24

        prefix_len = int(subnet.split("/")[1])
        total_ips = 2 ** (32 - prefix_len)
        # Subtract: network address, broadcast address, gateway
        usable = total_ips - 3
        return max(0, usable)
    except (ValueError, IndexError):
        return 253  # Default to /24 on error
