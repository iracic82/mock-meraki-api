"""
Device data generator for Mock Meraki API.

Generates realistic Meraki device data including:
- Proper serial number formats (Q2XX-XXXX-XXXX)
- Meraki OUI MAC addresses (00:18:0A)
- Real model numbers and firmware versions
- Realistic IP addresses and locations
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional

# Meraki OUI (Organizationally Unique Identifier)
MERAKI_OUI = "00:18:0A"

# Device models by product type with serial prefixes
DEVICE_MODELS = {
    "appliance": {
        "prefix": "Q2",
        "models": {
            "MX450": {"firmware": ["MX 18.107", "MX 18.106", "MX 17.12"], "ports": 10},
            "MX250": {"firmware": ["MX 18.107", "MX 18.106"], "ports": 8},
            "MX85": {"firmware": ["MX 18.107", "MX 18.106", "MX 17.12"], "ports": 6},
            "MX75": {"firmware": ["MX 18.107", "MX 18.106"], "ports": 6},
            "MX68": {"firmware": ["MX 18.107", "MX 18.106", "MX 17.12"], "ports": 4},
            "MX68W": {"firmware": ["MX 18.107", "MX 18.106"], "ports": 4},
            "MX67": {"firmware": ["MX 18.107", "MX 18.106"], "ports": 4},
            "MX67C": {"firmware": ["MX 18.107", "MX 18.106"], "ports": 4},
        }
    },
    "switch": {
        "prefix": "Q2",
        "models": {
            "MS425-32": {"firmware": ["MS 15.21", "MS 15.20", "MS 14.33"], "ports": 32},
            "MS350-48": {"firmware": ["MS 15.21", "MS 15.20"], "ports": 48},
            "MS250-48": {"firmware": ["MS 15.21", "MS 15.20", "MS 14.33"], "ports": 48},
            "MS225-48": {"firmware": ["MS 15.21", "MS 15.20"], "ports": 48},
            "MS225-24": {"firmware": ["MS 15.21", "MS 15.20"], "ports": 24},
            "MS120-24": {"firmware": ["MS 15.21", "MS 15.20", "MS 14.33"], "ports": 24},
            "MS120-8": {"firmware": ["MS 15.21", "MS 15.20"], "ports": 8},
        }
    },
    "wireless": {
        "prefix": "Q2",
        "models": {
            "MR57": {"firmware": ["MR 30.5", "MR 29.7", "MR 28.8"], "band": "Wi-Fi 6E"},
            "MR56": {"firmware": ["MR 30.5", "MR 29.7"], "band": "Wi-Fi 6"},
            "MR46": {"firmware": ["MR 30.5", "MR 29.7", "MR 28.8"], "band": "Wi-Fi 6"},
            "MR36": {"firmware": ["MR 30.5", "MR 29.7"], "band": "Wi-Fi 6"},
            "MR33": {"firmware": ["MR 30.5", "MR 29.7", "MR 28.8"], "band": "Wi-Fi 5"},
            "MR30H": {"firmware": ["MR 30.5", "MR 29.7"], "band": "Wi-Fi 5"},
        }
    },
    "cellularGateway": {
        "prefix": "Q2",
        "models": {
            "MG41": {"firmware": ["MG 1.24.2", "MG 1.23.1"], "bands": "LTE Cat 18"},
            "MG21": {"firmware": ["MG 1.24.2", "MG 1.23.1"], "bands": "LTE Cat 6"},
        }
    },
    "sensor": {
        "prefix": "Q3",
        "models": {
            "MT10": {"firmware": ["MT 1.0.3"], "type": "Temperature/Humidity"},
            "MT12": {"firmware": ["MT 1.0.3"], "type": "Water Leak"},
            "MT14": {"firmware": ["MT 1.0.3"], "type": "Door"},
        }
    },
    "camera": {
        "prefix": "Q2",
        "models": {
            "MV12W": {"firmware": ["MV 4.18"], "resolution": "1080p"},
            "MV22": {"firmware": ["MV 4.18"], "resolution": "1080p"},
            "MV72": {"firmware": ["MV 4.18"], "resolution": "4K"},
        }
    }
}

# US office locations with realistic coordinates
US_LOCATIONS = [
    {"city": "San Francisco", "state": "CA", "lat": 37.7749, "lng": -122.4194, "tz": "America/Los_Angeles"},
    {"city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060, "tz": "America/New_York"},
    {"city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298, "tz": "America/Chicago"},
    {"city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437, "tz": "America/Los_Angeles"},
    {"city": "Seattle", "state": "WA", "lat": 47.6062, "lng": -122.3321, "tz": "America/Los_Angeles"},
    {"city": "Austin", "state": "TX", "lat": 30.2672, "lng": -97.7431, "tz": "America/Chicago"},
    {"city": "Denver", "state": "CO", "lat": 39.7392, "lng": -104.9903, "tz": "America/Denver"},
    {"city": "Boston", "state": "MA", "lat": 42.3601, "lng": -71.0589, "tz": "America/New_York"},
    {"city": "Atlanta", "state": "GA", "lat": 33.7490, "lng": -84.3880, "tz": "America/New_York"},
    {"city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918, "tz": "America/New_York"},
    {"city": "Dallas", "state": "TX", "lat": 32.7767, "lng": -96.7970, "tz": "America/Chicago"},
    {"city": "Phoenix", "state": "AZ", "lat": 33.4484, "lng": -112.0740, "tz": "America/Phoenix"},
    {"city": "Portland", "state": "OR", "lat": 45.5152, "lng": -122.6784, "tz": "America/Los_Angeles"},
    {"city": "Minneapolis", "state": "MN", "lat": 44.9778, "lng": -93.2650, "tz": "America/Chicago"},
    {"city": "Detroit", "state": "MI", "lat": 42.3314, "lng": -83.0458, "tz": "America/Detroit"},
    {"city": "Philadelphia", "state": "PA", "lat": 39.9526, "lng": -75.1652, "tz": "America/New_York"},
    {"city": "San Diego", "state": "CA", "lat": 32.7157, "lng": -117.1611, "tz": "America/Los_Angeles"},
    {"city": "Houston", "state": "TX", "lat": 29.7604, "lng": -95.3698, "tz": "America/Chicago"},
    {"city": "Charlotte", "state": "NC", "lat": 35.2271, "lng": -80.8431, "tz": "America/New_York"},
    {"city": "Salt Lake City", "state": "UT", "lat": 40.7608, "lng": -111.8910, "tz": "America/Denver"},
]


class DeviceGenerator:
    """Generator for realistic Meraki device data."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
        self._serial_counter = 0
        self._mac_counter = 0

    def _generate_serial(self, prefix: str = "Q2") -> str:
        """Generate a Meraki-style serial number."""
        # Format: Q2XX-XXXX-XXXX
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}{part1}-{part2}-{part3}"

    def _generate_mac(self) -> str:
        """Generate a Meraki MAC address with proper OUI."""
        # Format: 00:18:0A:XX:XX:XX
        suffix = ':'.join(f'{random.randint(0, 255):02x}' for _ in range(3))
        return f"{MERAKI_OUI}:{suffix}"

    def _generate_lan_ip(self, network_octet: int, device_index: int) -> str:
        """Generate a LAN IP address."""
        third = device_index // 254
        fourth = (device_index % 254) + 1
        return f"10.{network_octet}.{third}.{fourth}"

    def _generate_wan_ip(self) -> str:
        """Generate a realistic public WAN IP."""
        return f"{random.randint(50, 200)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

    def generate_device(
        self,
        network_id: str,
        organization_id: str,
        product_type: str,
        model: str,
        name: str,
        location: dict,
        network_octet: int = 0,
        device_index: int = 0,
        tags: Optional[list] = None
    ) -> dict:
        """
        Generate a single device with realistic attributes.

        Args:
            network_id: Parent network ID
            organization_id: Parent organization ID
            product_type: Device type (appliance, switch, wireless, etc.)
            model: Specific model (MX450, MS225-48, MR57, etc.)
            name: Device name
            location: Location dict with city, lat, lng, tz
            network_octet: Second octet for IP addressing
            device_index: Index for IP addressing
            tags: Optional list of tags

        Returns:
            Device data dictionary
        """
        model_info = DEVICE_MODELS.get(product_type, {}).get("models", {}).get(model, {})
        prefix = DEVICE_MODELS.get(product_type, {}).get("prefix", "Q2")
        firmware = random.choice(model_info.get("firmware", ["unknown"]))

        serial = self._generate_serial(prefix)
        mac = self._generate_mac()
        lan_ip = self._generate_lan_ip(network_octet, device_index)

        device = {
            "serial": serial,
            "name": name,
            "mac": mac,
            "networkId": network_id,
            "organizationId": organization_id,
            "model": model,
            "productType": product_type,
            "firmware": firmware,
            "lanIp": lan_ip,
            "tags": tags or [],
            "lat": location.get("lat", 37.7749) + random.uniform(-0.01, 0.01),
            "lng": location.get("lng", -122.4194) + random.uniform(-0.01, 0.01),
            "address": f"{random.randint(100, 9999)} {location.get('city', 'Unknown')} St",
            "notes": None,  # Real API uses null, not empty string
            "url": f"https://mock.meraki.com/devices/{serial}/manage",
            "configurationUpdatedAt": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat() + "Z",
            "details": [],  # Additional device properties (name/value pairs)
        }

        # Add WAN IP for appliances
        if product_type == "appliance":
            device["wan1Ip"] = self._generate_wan_ip()
            if random.random() > 0.7:  # 30% have WAN2
                device["wan2Ip"] = self._generate_wan_ip()

        # Add IMEI for cellular devices
        if product_type == "cellularGateway":
            device["imei"] = ''.join(random.choices(string.digits, k=15))

        return device

    def generate_device_availability(self, device: dict) -> dict:
        """
        Generate device availability status.

        Matches Meraki API format: GET /organizations/{orgId}/devices/availabilities

        Args:
            device: Device data dictionary

        Returns:
            Device availability data dictionary per Meraki API format
        """
        # 95% of devices are online
        status = "online" if random.random() < 0.95 else random.choice(["alerting", "offline", "dormant"])

        return {
            "serial": device["serial"],
            "name": device["name"],
            "mac": device["mac"],
            "network": {
                "id": device["networkId"]
            },
            "productType": device["productType"],
            "status": status,
            "tags": device.get("tags", [])
        }

    def generate_devices_for_network(
        self,
        network_id: str,
        organization_id: str,
        location: dict,
        config: dict,
        network_octet: int = 0
    ) -> tuple[list[dict], list[dict]]:
        """
        Generate all devices for a network based on configuration.

        Args:
            network_id: Network ID
            organization_id: Organization ID
            location: Location information
            config: Dictionary with device counts per type
            network_octet: Octet for IP addressing

        Returns:
            Tuple of (devices list, availabilities list)

        Config format:
            {
                "appliances": [{"model": "MX68", "name": "Branch-MX"}],
                "switches": [{"model": "MS225-48", "count": 2, "name_prefix": "SW"}],
                "wireless": [{"model": "MR46", "count": 4, "name_prefix": "AP"}],
            }
        """
        devices = []
        availabilities = []
        device_index = 0

        # Generate appliances
        for appliance_config in config.get("appliances", []):
            model = appliance_config.get("model", "MX68")
            name = appliance_config.get("name", f"{network_id}-MX")
            device = self.generate_device(
                network_id=network_id,
                organization_id=organization_id,
                product_type="appliance",
                model=model,
                name=name,
                location=location,
                network_octet=network_octet,
                device_index=device_index,
                tags=appliance_config.get("tags", [])
            )
            devices.append(device)
            availabilities.append(self.generate_device_availability(device))
            device_index += 1

        # Generate switches
        for switch_config in config.get("switches", []):
            model = switch_config.get("model", "MS225-48")
            count = switch_config.get("count", 1)
            name_prefix = switch_config.get("name_prefix", "SW")
            for i in range(count):
                device = self.generate_device(
                    network_id=network_id,
                    organization_id=organization_id,
                    product_type="switch",
                    model=model,
                    name=f"{name_prefix}-{i + 1:02d}",
                    location=location,
                    network_octet=network_octet,
                    device_index=device_index,
                    tags=switch_config.get("tags", [])
                )
                devices.append(device)
                availabilities.append(self.generate_device_availability(device))
                device_index += 1

        # Generate wireless APs
        for wireless_config in config.get("wireless", []):
            model = wireless_config.get("model", "MR46")
            count = wireless_config.get("count", 1)
            name_prefix = wireless_config.get("name_prefix", "AP")
            for i in range(count):
                device = self.generate_device(
                    network_id=network_id,
                    organization_id=organization_id,
                    product_type="wireless",
                    model=model,
                    name=f"{name_prefix}-{i + 1:02d}",
                    location=location,
                    network_octet=network_octet,
                    device_index=device_index,
                    tags=wireless_config.get("tags", [])
                )
                devices.append(device)
                availabilities.append(self.generate_device_availability(device))
                device_index += 1

        # Generate cellular gateways
        for cellular_config in config.get("cellular", []):
            model = cellular_config.get("model", "MG41")
            name = cellular_config.get("name", f"{network_id}-MG")
            device = self.generate_device(
                network_id=network_id,
                organization_id=organization_id,
                product_type="cellularGateway",
                model=model,
                name=name,
                location=location,
                network_octet=network_octet,
                device_index=device_index,
                tags=cellular_config.get("tags", [])
            )
            devices.append(device)
            availabilities.append(self.generate_device_availability(device))
            device_index += 1

        return devices, availabilities
