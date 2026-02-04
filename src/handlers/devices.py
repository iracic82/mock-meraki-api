"""
Device-level endpoint handlers for Mock Meraki API.

Handles:
- GET /devices/{serial}/clients
"""

import json
import logging
from typing import Any

from db.dynamodb import (
    DynamoDBClient,
    ENTITY_DEVICE,
    ENTITY_CLIENT,
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
