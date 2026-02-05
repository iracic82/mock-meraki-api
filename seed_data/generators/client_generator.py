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
        """Generate a MAC address with the given OUI (lowercase like real Meraki API)."""
        suffix = ':'.join(f'{random.randint(0, 255):02x}' for _ in range(3))
        return f"{oui.lower()}:{suffix}"

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

    def _is_iot_device(self, hostname: str, device_type_prediction: str) -> bool:
        """Determine if a device is an IoT device based on hostname and type prediction.

        IoT devices: printers, scanners, sensors, cameras, VoIP phones
        Non-IoT: laptops, desktops, phones, tablets (user devices)
        """
        hostname_upper = hostname.upper()
        type_lower = device_type_prediction.lower() if device_type_prediction else ""

        # IoT device patterns
        iot_patterns = [
            "PRINTER", "SCANNER", "SENSOR", "CAMERA", "VOIP",
            "NUC", "DEVICE-"  # Generic devices are often IoT
        ]
        iot_type_patterns = [
            "printer", "scanner", "sensor", "camera", "ip phone",
            "iot", "intel nuc"
        ]

        # Check hostname
        for pattern in iot_patterns:
            if pattern in hostname_upper:
                return True

        # Check device type prediction
        for pattern in iot_type_patterns:
            if pattern in type_lower:
                return True

        return False

    def _get_ssid_for_device(self, hostname: str, device_type_prediction: str, named_vlan: str) -> str:
        """Determine appropriate SSID based on device type.

        - IoT devices (printers, sensors, cameras) → "IoT"
        - User devices on Guest VLAN → "Guest"
        - User devices on Corporate/other VLANs → "Corporate" (90%) or "Guest" (10%)
        """
        if self._is_iot_device(hostname, device_type_prediction):
            return "IoT"

        # User devices - check VLAN for Guest
        if named_vlan and "guest" in named_vlan.lower():
            return "Guest"

        # Corporate users - mostly Corporate SSID, some Guest
        return "Corporate" if random.random() < 0.9 else "Guest"

    def _generate_user(self) -> str:
        """Generate a realistic username."""
        first_names = ["john", "jane", "mike", "sarah", "david", "lisa", "tom", "anna", "chris", "kate"]
        last_names = ["smith", "jones", "wilson", "brown", "davis", "miller", "moore", "taylor", "anderson", "thomas"]
        return f"{random.choice(first_names)}.{random.choice(last_names)}"

    def _get_vlan_name(self, vlan_id) -> str:
        """Get descriptive VLAN name based on ID."""
        # Ensure vlan_id is an integer
        try:
            vid = int(vlan_id)
        except (ValueError, TypeError):
            return f"VLAN {vlan_id}"

        # Map common VLAN IDs to descriptive names
        vlan_names = {
            1: "Default",
            10: "Corporate",
            11: "Corporate",
            12: "Corporate",
            13: "Corporate",
            20: "Corporate",
            21: "Corporate",
            30: "Guest",
            31: "Guest",
            40: "Voice",
            41: "Voice",
            50: "Servers",
            60: "IoT",
            70: "Management",
            80: "Wireless",
            90: "Security",
            99: "Management",
            100: "Data",
        }
        # For unmapped VLANs, generate descriptive name based on range
        if vid in vlan_names:
            return vlan_names[vid]
        elif vid < 20:
            return "Corporate"
        elif vid < 40:
            return "Guest"
        elif vid < 60:
            return "Voice"
        elif vid < 80:
            return "IoT"
        elif vid < 100:
            return "Management"
        else:
            return "Data"

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
            "namedVlan": self._get_vlan_name(vlan_id),
            "switchport": f"GigabitEthernet1/0/{random.randint(1, 48)}" if random.random() > 0.4 else None,
            "ssid": None,  # Will be set for wireless clients
            "status": "Online" if random.random() > 0.1 else "Offline",
            "notes": random.choice([None, None, None, "Visitor device", "Temp access", "Executive laptop", "Conference room"]),
            "smInstalled": random.random() > 0.8,
            "recentDeviceSerial": device_serial,
            "recentDeviceName": None,
            "recentDeviceMac": None,
            "recentDeviceConnection": "Wired" if random.random() > 0.4 else "Wireless",
            "wirelessCapabilities": None,
            "adaptivePolicyGroup": random.choice([None, None, "1: Employee", "2: Infrastructure", "3: Guest", "4: IoT Devices"]),
            "groupPolicy8021x": random.choice([None, None, None, "Employee_Access", "Guest_Access", "Contractor_Access", "Student_Access"]),
            "pskGroup": random.choice([None, None, None, "Group 1", "Group 2", "IoT Group"]),
            "usage": {
                "sent": sent,
                "recv": recv,
                "total": sent + recv
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
                "sent": int(base_client["usage"]["sent"] / 1000),  # Convert to KB (integer) for device endpoint
                "recv": int(base_client["usage"]["recv"] / 1000)
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

        # Build device lookup map for getting name and MAC
        device_lookup = {d["serial"]: d for d in devices}

        # Separate devices by type - wired clients connect to switches, wireless to APs
        switches = [d for d in devices if d["productType"] == "switch"]
        access_points = [d for d in devices if d["productType"] == "wireless"]

        # Determine connection distribution based on available devices
        # If only APs exist, all clients are wireless
        # If only switches exist, all clients are wired
        # If both exist, distribute ~60% wired, ~40% wireless
        has_switches = len(switches) > 0
        has_aps = len(access_points) > 0

        for i in range(count):
            # Pick a VLAN (weighted towards corporate/data VLANs)
            vlan = random.choice(vlans) if vlans else {"id": 1, "name": "Default", "subnet": "192.168.1.0/24"}
            vlan_id = vlan.get("id", 1)
            vlan_name = vlan.get("name", "Default")  # Get actual VLAN name from topology
            vlan_subnet = vlan.get("subnet")  # Get the actual subnet (e.g., '192.168.100.0/24')

            # Generate client ID
            client_id = f"k{random.randint(100000, 999999)}"

            # Generate network client first to get hostname/device type
            net_client = self.generate_network_client(
                client_id=client_id,
                network_id=network_id,
                vlan_id=vlan_id,
                client_index=i,
                vlan_subnet=vlan_subnet
            )
            # Override namedVlan with actual VLAN name from topology
            net_client["namedVlan"] = vlan_name

            # Determine connection type based on DEVICE TYPE (realistic assignment)
            hostname = net_client.get("description", "").upper()
            device_prediction = net_client.get("deviceTypePrediction", "").lower()

            # Always wireless: phones, tablets
            always_wireless = any(p in hostname for p in ["IPHONE", "IPAD", "GALAXY", "PIXEL", "SAMSUNG-TAB", "TABLET"])
            always_wireless = always_wireless or any(p in device_prediction for p in ["iphone", "ipad", "galaxy", "pixel", "tablet", "android"])

            # Always wired: desktops, printers, scanners, VoIP, sensors, cameras, NUCs
            always_wired = any(p in hostname for p in ["DESKTOP", "PRINTER", "SCANNER", "VOIP", "SENSOR", "CAMERA", "NUC"])
            always_wired = always_wired or any(p in device_prediction for p in ["desktop", "printer", "scanner", "ip phone", "voip", "sensor", "camera", "nuc"])

            # Determine is_wired based on device type
            if always_wireless:
                is_wired = False
            elif always_wired:
                is_wired = True
            else:
                # Laptops, Chromebooks, MacBooks, ThinkPads, Surfaces - mix (40% wired, 60% wireless)
                is_wired = random.random() < 0.4

            # Adjust based on available infrastructure
            if is_wired and not has_switches:
                is_wired = False  # Force wireless if no switches
            if not is_wired and not has_aps:
                is_wired = True  # Force wired if no APs

            # Pick appropriate device based on connection type
            if is_wired and has_switches:
                device = random.choice(switches)
                connection_type = "Wired"
            elif not is_wired and has_aps:
                device = random.choice(access_points)
                connection_type = "Wireless"
            elif has_switches:
                device = random.choice(switches)
                connection_type = "Wired"
            elif has_aps:
                device = random.choice(access_points)
                connection_type = "Wireless"
            else:
                device = None
                connection_type = "Wired" if is_wired else "Wireless"

            device_serial = device["serial"] if device else None
            device_name = device.get("name") if device else None
            device_mac = device.get("mac") if device else None

            # Set connection info on the already-generated client
            net_client["recentDeviceSerial"] = device_serial
            net_client["recentDeviceName"] = device_name
            net_client["recentDeviceMac"] = device_mac
            net_client["recentDeviceConnection"] = connection_type

            # Use actual VLAN name for SSID determination
            client_named_vlan = vlan_name

            # Set connection-specific fields
            if connection_type == "Wired":
                # Wired clients have switchport, no SSID (matches real Meraki API)
                net_client["switchport"] = f"GigabitEthernet1/0/{random.randint(1, 48)}"
                net_client["ssid"] = None
                net_client["wirelessCapabilities"] = None
            else:
                # Wireless clients have SSID based on device type, no switchport
                net_client["switchport"] = None
                net_client["ssid"] = self._get_ssid_for_device(hostname, device_prediction, client_named_vlan)
                net_client["wirelessCapabilities"] = random.choice([
                    "802.11ac - 2.4 GHz",
                    "802.11ac - 5 GHz",
                    "802.11ax - 2.4 GHz",
                    "802.11ax - 5 GHz",
                    "802.11ax - 6 GHz",
                    "802.11n - 2.4 GHz"
                ])

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
                # Ensure switchport consistency for device client too
                if connection_type == "Wired":
                    dev_client["switchport"] = net_client["switchport"]
                else:
                    dev_client["switchport"] = None
                device_clients[device_serial].append(dev_client)

        return network_clients, device_clients
