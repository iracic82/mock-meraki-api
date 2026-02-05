"""
Organization-level endpoint handlers for Mock Meraki API.

Handles:
- GET /organizations
- GET /organizations/{organizationId}/networks
- GET /organizations/{organizationId}/devices
- GET /organizations/{organizationId}/devices/availabilities
- GET /organizations/{organizationId}/devices/statuses
"""

import json
import logging
from typing import Any

from db.dynamodb import (
    DynamoDBClient,
    ENTITY_ORGANIZATION,
    ENTITY_NETWORK,
    ENTITY_DEVICE,
    ENTITY_DEVICE_AVAILABILITY,
    ENTITY_DEVICE_STATUS,
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


def get_organizations(topology: str) -> dict:
    """
    Get all organizations for the specified topology.

    Returns:
        API Gateway response with list of organizations
    """
    logger.info(f"Getting organizations for topology: {topology}")

    db = DynamoDBClient()
    organizations = db.get_entities(topology, ENTITY_ORGANIZATION)

    if not organizations:
        logger.warning(f"No organizations found for topology: {topology}")
        return _response(200, [])

    logger.info(f"Returning {len(organizations)} organizations")
    return _response(200, organizations)


def get_organization_networks(topology: str, organization_id: str) -> dict:
    """
    Get all networks for a specific organization.

    Args:
        topology: Active topology name
        organization_id: Organization ID

    Returns:
        API Gateway response with list of networks
    """
    logger.info(f"Getting networks for org {organization_id} in topology {topology}")

    db = DynamoDBClient()

    # First verify organization exists
    org = db.get_entity(topology, ENTITY_ORGANIZATION, organization_id)
    if not org:
        return _response(404, {"errors": [f"Organization {organization_id} not found"]})

    # Get networks by parent organization
    networks = db.get_entities_by_parent(
        topology, ENTITY_ORGANIZATION, organization_id, ENTITY_NETWORK
    )

    logger.info(f"Returning {len(networks)} networks")
    return _response(200, networks)


def get_organization_devices(topology: str, organization_id: str) -> dict:
    """
    Get all devices for a specific organization.

    Args:
        topology: Active topology name
        organization_id: Organization ID

    Returns:
        API Gateway response with list of devices
    """
    logger.info(f"Getting devices for org {organization_id} in topology {topology}")

    db = DynamoDBClient()

    # First verify organization exists
    org = db.get_entity(topology, ENTITY_ORGANIZATION, organization_id)
    if not org:
        return _response(404, {"errors": [f"Organization {organization_id} not found"]})

    # Get devices by parent organization
    devices = db.get_entities_by_parent(
        topology, ENTITY_ORGANIZATION, organization_id, ENTITY_DEVICE
    )

    logger.info(f"Returning {len(devices)} devices")
    return _response(200, devices)


def get_organization_devices_availabilities(topology: str, organization_id: str) -> dict:
    """
    Get device availability status for all devices in an organization.

    Args:
        topology: Active topology name
        organization_id: Organization ID

    Returns:
        API Gateway response with list of device availabilities
    """
    logger.info(f"Getting device availabilities for org {organization_id}")

    db = DynamoDBClient()

    # First verify organization exists
    org = db.get_entity(topology, ENTITY_ORGANIZATION, organization_id)
    if not org:
        return _response(404, {"errors": [f"Organization {organization_id} not found"]})

    # Get device availabilities by parent organization
    availabilities = db.get_entities_by_parent(
        topology, ENTITY_ORGANIZATION, organization_id, ENTITY_DEVICE_AVAILABILITY
    )

    logger.info(f"Returning {len(availabilities)} device availabilities")
    return _response(200, availabilities)


def get_organization_devices_statuses(topology: str, organization_id: str) -> dict:
    """
    Get device statuses for all devices in an organization.

    This endpoint returns detailed device status information including:
    - lastReportedAt: ISO 8601 timestamp of last device check-in
    - status: online, offline, alerting, or dormant
    - lanIp, gateway, publicIp: Network connectivity details
    - ipType, primaryDns, secondaryDns: Network configuration
    - components: Hardware components like power supplies (for switches)

    Official Meraki API: GET /organizations/{organizationId}/devices/statuses

    Args:
        topology: Active topology name
        organization_id: Organization ID

    Returns:
        API Gateway response with list of device statuses
    """
    logger.info(f"Getting device statuses for org {organization_id}")

    db = DynamoDBClient()

    # First verify organization exists
    org = db.get_entity(topology, ENTITY_ORGANIZATION, organization_id)
    if not org:
        return _response(404, {"errors": [f"Organization {organization_id} not found"]})

    # Get device statuses by parent organization
    statuses = db.get_entities_by_parent(
        topology, ENTITY_ORGANIZATION, organization_id, ENTITY_DEVICE_STATUS
    )

    logger.info(f"Returning {len(statuses)} device statuses")
    return _response(200, statuses)
