"""
Client data generator for Mock Meraki API.

Generates realistic client data including:
- Diverse manufacturers and device types
- Realistic MAC addresses
- Proper usage statistics
- VLAN assignments
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional

# Client manufacturers with realistic distributions and VERIFIED OUI prefixes
# OUIs verified against IEEE/Wireshark OUI database
CLIENT_MANUFACTURERS = [
    {"name": "Apple", "oui": "3C:E0:72", "weight": 25, "os": ["iOS 17", "iOS 16", "macOS Sonoma", "macOS Ventura"]},  # Real Apple OUI
    {"name": "Samsung", "oui": "84:25:DB", "weight": 15, "os": ["Android 14", "Android 13", "Android 12"]},  # Real Samsung OUI
    {"name": "Dell", "oui": "18:A9:05", "weight": 12, "os": ["Windows 11", "Windows 10"]},  # Real Dell OUI
    {"name": "HP", "oui": "3C:D9:2B", "weight": 10, "os": ["Windows 11", "Windows 10"]},  # Real HP OUI
    {"name": "Lenovo", "oui": "28:D2:44", "weight": 10, "os": ["Windows 11", "Windows 10", "Chrome OS"]},  # Real Lenovo OUI
    {"name": "Microsoft", "oui": "28:18:78", "weight": 5, "os": ["Windows 11", "Windows 10"]},  # Real Microsoft OUI
    {"name": "Intel", "oui": "3C:97:0E", "weight": 5, "os": ["Windows 11", "Windows 10", "Linux"]},  # Real Intel OUI
    {"name": "Google", "oui": "F4:F5:D8", "weight": 5, "os": ["Android 14", "Chrome OS"]},  # Real Google OUI
    {"name": "Cisco", "oui": "00:1B:0D", "weight": 3, "os": ["IOS-XE", "AireOS"]},  # Real Cisco OUI
    {"name": "Zebra", "oui": "00:A0:F8", "weight": 3, "os": ["Android 11", "Android 10"]},  # Real Zebra OUI
    {"name": "Honeywell", "oui": "00:40:84", "weight": 2, "os": ["Android 10"]},  # Real Honeywell OUI
    {"name": "Epson", "oui": "00:26:AB", "weight": 2, "os": ["Embedded"]},  # Real Epson OUI
    {"name": "Canon", "oui": "00:1E:8F", "weight": 2, "os": ["Embedded"]},  # Real Canon OUI
    {"name": "IoT Device", "oui": "B8:27:EB", "weight": 1, "os": ["Linux", "Embedded"]},  # Raspberry Pi Foundation
]

# Device types with usage patterns
DEVICE_TYPES = [
    {"type": "Laptop", "weight": 35, "sent_range": (500_000_000, 5_000_000_000), "recv_range": (1_000_000_000, 10_000_000_000)},
    {"type": "Smartphone", "weight": 25, "sent_range": (50_000_000, 500_000_000), "recv_range": (200_000_000, 2_000_000_000)},
    {"type": "Desktop", "weight": 15, "sent_range": (1_000_000_000, 10_000_000_000), "recv_range": (2_000_000_000, 20_000_000_000)},
    {"type": "Tablet", "weight": 10, "sent_range": (100_000_000, 1_000_000_000), "recv_range": (500_000_000, 5_000_000_000)},
    {"type": "Printer", "weight": 5, "sent_range": (1_000_000, 50_000_000), "recv_range": (10_000_000, 100_000_000)},
    {"type": "VoIP Phone", "weight": 5, "sent_range": (500_000_000, 2_000_000_000), "recv_range": (500_000_000, 2_000_000_000)},
    {"type": "IoT Sensor", "weight": 3, "sent_range": (1_000_000, 10_000_000), "recv_range": (5_000_000, 50_000_000)},
    {"type": "Camera", "weight": 2, "sent_range": (5_000_000_000, 50_000_000_000), "recv_range": (10_000_000, 100_000_000)},
]

# Common hostnames/descriptions
HOSTNAME_PREFIXES = [
    "LAPTOP", "DESKTOP", "PHONE", "IPHONE", "MACBOOK", "SURFACE", "PRINTER",
    "SCANNER", "TABLET", "IPAD", "GALAXY", "PIXEL", "VOIP", "CAMERA", "SENSOR"
]


class ClientGenerator:
    """Generator for realistic network client data."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)

        # Build weighted lists for random selection
        self._manufacturers = []
        for m in CLIENT_MANUFACTURERS:
            self._manufacturers.extend([m] * m["weight"])

        self._device_types = []
        for d in DEVICE_TYPES:
            self._device_types.extend([d] * d["weight"])

    def _generate_mac(self, oui: str) -> str:
        """Generate a MAC address with the given OUI."""
        suffix = ':'.join(f'{random.randint(0, 255):02x}'.upper() for _ in range(3))
        return f"{oui}:{suffix}"

    def _generate_ip_from_subnet(self, subnet: str, client_index: int) -> str:
        """Generate a client IP address from the VLAN's actual subnet.

        Args:
            subnet: VLAN subnet in CIDR notation (e.g., '192.168.100.0/24')
            client_index: Index for the fourth octet

        Returns:
            IP address within the subnet (e.g., '192.168.100.5')
        """
        # Parse subnet to get base (e.g., '192.168.100.0/24' -> '192.168.100')
        base = subnet.split('/')[0].rsplit('.', 1)[0]
        fourth = (client_index % 250) + 2  # Start from .2, leave .1 for gateway
        return f"{base}.{fourth}"

    def _generate_hostname_and_type(self, manufacturer: str, os: str) -> tuple[str, str]:
        """Generate a realistic hostname and Meraki-style deviceTypePrediction."""
        # Map manufacturer to hostname prefixes with Meraki-style device type predictions
        # Meraki returns detailed strings like "iPhone SE, iOS9.3.5"
        prefixes = {
            "Apple": [
                ("IPHONE", lambda o: f"iPhone, {o}"),
                ("MACBOOK", lambda o: f"MacBook Pro, {o}"),
                ("IPAD", lambda o: f"iPad, {o}"),
            ],
            "Samsung": [
                ("GALAXY", lambda o: f"Samsung Galaxy, {o}"),
                ("SAMSUNG-TAB", lambda o: f"Samsung Tablet, {o}"),
            ],
            "Dell": [
                ("DELL-LAPTOP", lambda o: f"Dell Laptop, {o}"),
                ("DELL-DESKTOP", lambda o: f"Dell Desktop, {o}"),
            ],
            "HP": [
                ("HP-LAPTOP", lambda o: f"HP Laptop, {o}"),
                ("HP-PRINTER", lambda o: "HP Printer"),
            ],
            "Lenovo": [
                ("LENOVO", lambda o: f"Lenovo ThinkPad, {o}"),
                ("THINKPAD", lambda o: f"Lenovo ThinkPad, {o}"),
            ],
            "Microsoft": [
                ("SURFACE", lambda o: f"Microsoft Surface, {o}"),
                ("DEVICE", lambda o: f"Windows PC, {o}"),
            ],
            "Google": [
                ("PIXEL", lambda o: f"Google Pixel, {o}"),
                ("CHROMEBOOK", lambda o: f"Chromebook, {o}"),
            ],
            "Cisco": [
                ("VOIP", lambda o: "Cisco IP Phone"),
                ("DEVICE", lambda o: "Cisco Device"),
            ],
            "Zebra": [
                ("SCANNER", lambda o: "Zebra Scanner"),
                ("DEVICE", lambda o: f"Zebra Device, {o}"),
            ],
            "Honeywell": [
                ("SCANNER", lambda o: "Honeywell Scanner"),
                ("DEVICE", lambda o: f"Honeywell Device, {o}"),
            ],
            "Epson": [
                ("PRINTER", lambda o: "Epson Printer"),
            ],
            "Canon": [
                ("PRINTER", lambda o: "Canon Printer"),
            ],
            "IoT Device": [
                ("SENSOR", lambda o: "IoT Sensor"),
                ("CAMERA", lambda o: "IP Camera"),
            ],
            "Intel": [
                ("DEVICE", lambda o: f"Intel NUC, {o}"),
            ],
        }

        choices = prefixes.get(manufacturer, [("DEVICE", lambda o: f"Unknown Device, {o}")])
        prefix, type_func = random.choice(choices)
        device_type = type_func(os)
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}-{suffix}", device_type

    def _generate_user(self) -> str:
        """Generate a realistic username."""
        first_names = ["john", "jane", "mike", "sarah", "david", "lisa", "tom", "anna", "chris", "kate"]
        last_names = ["smith", "jones", "wilson", "brown", "davis", "miller", "moore", "taylor", "anderson", "thomas"]
        return f"{random.choice(first_names)}.{random.choice(last_names)}"

    def generate_client(
        self,
        client_id: str,
        network_id: str,
        vlan_id: int,
        client_index: int,
        device_serial: Optional[str] = None,
        vlan_subnet: Optional[str] = None
    ) -> dict:
        """
        Generate a single client with realistic attributes.

        Args:
            client_id: Unique client identifier
            network_id: Parent network ID
            vlan_id: VLAN ID for IP assignment
            client_index: Index for IP addressing
            device_serial: Optional device serial the client is connected to
            vlan_subnet: VLAN subnet in CIDR (e.g., '192.168.100.0/24') for correct IP

        Returns:
            Client data dictionary
        """
        manufacturer = random.choice(self._manufacturers)

        mac = self._generate_mac(manufacturer["oui"])
        # Use actual VLAN subnet if provided, otherwise fall back to VLAN ID
        if vlan_subnet:
            ip = self._generate_ip_from_subnet(vlan_subnet, client_index)
        else:
            # Fallback for backwards compatibility
            ip = f"192.168.{vlan_id}.{(client_index % 250) + 2}"
        os = random.choice(manufacturer["os"])
        hostname, device_type_prediction = self._generate_hostname_and_type(manufacturer["name"], os)

        # Calculate realistic timestamps (Unix timestamps as integers per Meraki API)
        now = datetime.utcnow()
        first_seen = now - timedelta(days=random.randint(1, 90))
        last_seen = now - timedelta(minutes=random.randint(0, 60))
        first_seen_ts = str(int(first_seen.timestamp()))
        last_seen_ts = str(int(last_seen.timestamp()))

        # Get usage pattern based on device type
        usage_patterns = {
            "Computer": {"sent_range": (500_000_000, 5_000_000_000), "recv_range": (1_000_000_000, 10_000_000_000)},
            "Phone": {"sent_range": (50_000_000, 500_000_000), "recv_range": (200_000_000, 2_000_000_000)},
            "Tablet": {"sent_range": (100_000_000, 1_000_000_000), "recv_range": (500_000_000, 5_000_000_000)},
            "Printer": {"sent_range": (1_000_000, 50_000_000), "recv_range": (10_000_000, 100_000_000)},
            "VoIP phone": {"sent_range": (500_000_000, 2_000_000_000), "recv_range": (500_000_000, 2_000_000_000)},
            "IP camera": {"sent_range": (5_000_000_000, 50_000_000_000), "recv_range": (10_000_000, 100_000_000)},
            "Other": {"sent_range": (1_000_000, 100_000_000), "recv_range": (5_000_000, 200_000_000)},
        }
        pattern = usage_patterns.get(device_type_prediction, usage_patterns["Other"])
        sent = random.randint(*pattern["sent_range"])
        recv = random.randint(*pattern["recv_range"])

        client = {
            "id": client_id,
            "mac": mac,
            "ip": ip,
            "ip6": None,
            "ip6Local": None,
            "description": hostname,
            "firstSeen": first_seen_ts,
            "lastSeen": last_seen_ts,
            "manufacturer": manufacturer["name"],
            "os": os,
            "deviceTypePrediction": device_type_prediction,
            "user": self._generate_user() if random.random() > 0.3 else None,
            "vlan": str(vlan_id),
            "namedVlan": f"VLAN_{vlan_id}",
            "switchport": f"Port {random.randint(1, 48)}" if random.random() > 0.3 else None,
            "ssid": None,  # Will be set for wireless clients
            "status": "Online" if random.random() > 0.1 else "Offline",
            "notes": None,
            "smInstalled": random.random() > 0.8,
            "recentDeviceSerial": device_serial,
            "recentDeviceName": None,
            "recentDeviceMac": None,
            "recentDeviceConnection": "Wired" if random.random() > 0.4 else "Wireless",
            "wirelessCapabilities": None,
            "adaptivePolicyGroup": None,
            "groupPolicy8021x": None,
            "pskGroup": None,
            "usage": {
                "sent": sent,
                "recv": recv
            }
        }

        # Add wireless-specific fields
        if client["recentDeviceConnection"] == "Wireless":
            client["ssid"] = random.choice(["Corporate", "Guest", "IoT"])
            client["switchport"] = None
            client["wirelessCapabilities"] = random.choice([
                "802.11ac - 2.4 GHz",
                "802.11ac - 5 GHz",
                "802.11ax - 2.4 GHz",
                "802.11ax - 5 GHz",
                "802.11ax - 6 GHz",
                "802.11n - 2.4 GHz"
            ])

        return client

    def generate_network_client(
        self,
        client_id: str,
        network_id: str,
        vlan_id: int,
        client_index: int,
        vlan_subnet: Optional[str] = None
    ) -> dict:
        """
        Generate a network-level client (for /networks/{id}/clients endpoint).

        This is the FULL client format with all fields including deviceTypePrediction.

        Args:
            client_id: Unique client identifier
            network_id: Parent network ID
            vlan_id: VLAN ID
            client_index: Index for IP addressing
            vlan_subnet: VLAN subnet in CIDR for correct IP assignment

        Returns:
            Network client data dictionary matching Meraki API format
        """
        base_client = self.generate_client(client_id, network_id, vlan_id, client_index, vlan_subnet=vlan_subnet)

        # Network clients include ALL fields per Meraki API
        return {
            "id": base_client["id"],
            "mac": base_client["mac"],
            "ip": base_client["ip"],
            "ip6": base_client["ip6"],
            "ip6Local": base_client["ip6Local"],
            "description": base_client["description"],
            "firstSeen": base_client["firstSeen"],
            "lastSeen": base_client["lastSeen"],
            "manufacturer": base_client["manufacturer"],
            "os": base_client["os"],
            "deviceTypePrediction": base_client["deviceTypePrediction"],
            "user": base_client["user"],
            "vlan": base_client["vlan"],
            "namedVlan": base_client["namedVlan"],
            "ssid": base_client["ssid"],
            "switchport": base_client["switchport"],
            "wirelessCapabilities": base_client["wirelessCapabilities"],
            "smInstalled": base_client["smInstalled"],
            "recentDeviceSerial": base_client["recentDeviceSerial"],
            "recentDeviceName": base_client["recentDeviceName"],
            "recentDeviceMac": base_client["recentDeviceMac"],
            "recentDeviceConnection": base_client["recentDeviceConnection"],
            "notes": base_client["notes"],
            "groupPolicy8021x": base_client["groupPolicy8021x"],
            "adaptivePolicyGroup": base_client["adaptivePolicyGroup"],
            "pskGroup": base_client["pskGroup"],
            "status": base_client["status"],
            "usage": base_client["usage"],
            # Internal field for seeding - not part of Meraki API response
            "_network_id": network_id
        }

    def generate_device_client(
        self,
        client_id: str,
        network_id: str,
        vlan_id: int,
        client_index: int,
        device_serial: str,
        vlan_subnet: Optional[str] = None
    ) -> dict:
        """
        Generate a device-level client (for /devices/{serial}/clients endpoint).

        This is a SIMPLIFIED format - Meraki device clients API does NOT include:
        deviceTypePrediction, manufacturer, os, firstSeen, lastSeen, status, recentDevice*

        Args:
            client_id: Unique client identifier
            network_id: Parent network ID
            vlan_id: VLAN ID
            client_index: Index for IP addressing
            device_serial: Device serial this client is connected to
            vlan_subnet: VLAN subnet in CIDR for correct IP assignment

        Returns:
            Device client data dictionary matching Meraki API format
        """
        base_client = self.generate_client(client_id, network_id, vlan_id, client_index, device_serial, vlan_subnet=vlan_subnet)

        # Device clients have SIMPLER structure per Meraki API docs
        return {
            "id": base_client["id"],
            "mac": base_client["mac"],
            "description": base_client["description"],
            "mdnsName": base_client["description"],  # Often same as description
            "dhcpHostname": base_client["description"].replace("-", "").upper()[:15],
            "user": base_client["user"],
            "ip": base_client["ip"],
            "vlan": base_client["vlan"],
            "namedVlan": base_client["namedVlan"],
            "switchport": base_client["switchport"],
            "adaptivePolicyGroup": base_client["adaptivePolicyGroup"],
            "usage": {
                "sent": base_client["usage"]["sent"] / 1000,  # Convert to KB for device endpoint
                "recv": base_client["usage"]["recv"] / 1000
            }
        }

    def generate_clients_for_network(
        self,
        network_id: str,
        vlans: list[dict],
        count: int,
        devices: list[dict]
    ) -> tuple[list[dict], dict[str, list[dict]]]:
        """
        Generate clients for a network, distributed across VLANs and devices.

        Args:
            network_id: Network ID
            vlans: List of VLAN configurations
            count: Total number of clients to generate
            devices: List of devices in the network

        Returns:
            Tuple of (network_clients, device_clients_map)
            - network_clients: List of clients for /networks/{id}/clients
            - device_clients_map: Dict mapping device serial to list of clients
        """
        network_clients = []
        device_clients = {d["serial"]: [] for d in devices if d["productType"] in ["switch", "wireless"]}

        # Get device serials that can have clients
        connectable_devices = [
            d["serial"] for d in devices
            if d["productType"] in ["switch", "wireless"]
        ]

        for i in range(count):
            # Pick a VLAN (weighted towards corporate/data VLANs)
            vlan = random.choice(vlans) if vlans else {"id": 1, "name": "Default", "subnet": "192.168.1.0/24"}
            vlan_id = vlan.get("id", 1)
            vlan_subnet = vlan.get("subnet")  # Get the actual subnet (e.g., '192.168.100.0/24')

            # Generate client ID
            client_id = f"k{random.randint(100000, 999999)}"

            # Pick a device this client is connected to
            device_serial = random.choice(connectable_devices) if connectable_devices else None

            # Generate network client with correct subnet-based IP
            net_client = self.generate_network_client(
                client_id=client_id,
                network_id=network_id,
                vlan_id=vlan_id,
                client_index=i,
                vlan_subnet=vlan_subnet
            )
            net_client["recentDeviceSerial"] = device_serial
            network_clients.append(net_client)

            # Generate device client (simpler format per Meraki API)
            if device_serial:
                dev_client = self.generate_device_client(
                    client_id=client_id,
                    network_id=network_id,
                    vlan_id=vlan_id,
                    client_index=i,
                    device_serial=device_serial,
                    vlan_subnet=vlan_subnet
                )
                device_clients[device_serial].append(dev_client)

        return network_clients, device_clients
