"""
Authentication middleware for Mock Meraki API.

Validates the X-Cisco-Meraki-API-Key header against API key stored in AWS Secrets Manager.
"""

import os
import logging
import secrets
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Meraki API key header name (lowercase for normalized headers)
API_KEY_HEADER = "x-cisco-meraki-api-key"


@lru_cache(maxsize=1)
def _get_api_key_from_secrets_manager() -> str:
    """
    Fetch API key from AWS Secrets Manager.
    Cached to avoid repeated calls.
    """
    secret_name = os.environ.get("API_KEY_SECRET_NAME", "meraki-mock-api/api-key")

    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except ClientError as e:
        logger.error(f"Failed to get API key from Secrets Manager: {e}")
        raise


def validate_api_key(headers: dict) -> dict:
    """
    Validate the Meraki API key from request headers.

    Args:
        headers: Dictionary of request headers (lowercase keys)

    Returns:
        dict with 'valid' boolean and optional 'error' message
    """
    # Debug: log all headers to see what InfoBlox sends
    logger.warning(f"DEBUG - All headers received: {list(headers.keys())}")

    # Check for API key in multiple possible header names
    api_key = headers.get(API_KEY_HEADER)

    # Also check Authorization header (Bearer token format)
    if not api_key:
        auth_header = headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            logger.warning("DEBUG - Found API key in Authorization Bearer header")

    if not api_key:
        logger.warning("Missing API key header")
        return {
            "valid": False,
            "error": "Missing API key. Please include 'X-Cisco-Meraki-API-Key' header."
        }

    try:
        required_key = _get_api_key_from_secrets_manager()
    except Exception as e:
        logger.error(f"Failed to retrieve API key: {e}")
        return {
            "valid": False,
            "error": "API authentication unavailable"
        }

    # Constant-time comparison to prevent timing attacks
    if secrets.compare_digest(api_key, required_key):
        logger.info("API key validated successfully")
        return {"valid": True}
    else:
        logger.warning("Invalid API key provided")
        return {
            "valid": False,
            "error": "Invalid API key"
        }
