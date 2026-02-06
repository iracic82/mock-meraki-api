# Mock Meraki API - Data Generation Guide

This document explains how to generate new topologies and seed data for the Mock Meraki API.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GENERATORS                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ NetworkGenerator│ DeviceGenerator │ ClientGenerator             │
│ - Organizations │ - Devices       │ - Network Clients           │
│ - Networks      │ - Availabilities│ - Device Clients            │
│ - VLANs         │ - Serial nums   │ - deviceTypePrediction      │
│ - VPN configs   │ - MAC addresses │ - Usage stats               │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TOPOLOGIES                                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ hub_spoke.py    │ mesh.py         │ multi_org.py                │
│ - 1 Org         │ - 1 Org         │ - 5 Orgs                    │
│ - 21 Networks   │ - 8 Networks    │ - 20 Networks               │
│ - 134 Devices   │ - 150+ Devices  │ - 200+ Devices              │
│ - 740 Clients   │ - 1500+ Clients │ - 2000+ Clients             │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    seed_dynamodb.py                              │
│                 Writes data to DynamoDB                          │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
seed_data/
├── generators/
│   ├── __init__.py
│   ├── device_generator.py    # Generates devices & availabilities
│   ├── client_generator.py    # Generates network & device clients
│   └── network_generator.py   # Generates orgs, networks, VLANs, VPN
├── topologies/
│   ├── __init__.py
│   ├── hub_spoke.py           # Enterprise hub-spoke VPN topology
│   ├── mesh.py                # Full mesh data center topology
│   └── multi_org.py           # Multi-tenant MSP topology
└── seed_dynamodb.py           # Main seeding script
```

## Generators

### 1. NetworkGenerator (`network_generator.py`)

Generates organizations, networks, VLANs, VLAN profiles, and VPN configurations.

```python
from seed_data.generators.network_generator import NetworkGenerator

gen = NetworkGenerator(seed=42)  # Optional seed for reproducibility

# Generate organization
org = gen.generate_organization(
    org_id="883652",
    name="Acme Corporation",
    region="North America"
)

# Generate network
network = gen.generate_network(
    network_id="N_HQ001",
    organization_id="883652",
    name="HQ-Campus",
    product_types=["appliance", "switch", "wireless"],
    timezone="America/Los_Angeles",
    tags=["hub", "headquarters"],
    notes="Corporate HQ"
)

# Generate VLANs
vlans = gen.generate_vlans_for_network(
    network_id="N_HQ001",
    vlan_types=["corporate", "guest", "voice", "iot", "management"],
    base_third_octet=10
)

# Generate VPN config
vpn = gen.generate_vpn_config(
    network_id="N_HQ001",
    mode="hub",  # or "spoke"
    subnets=[{"localSubnet": "192.168.10.0/24", "useVpn": True}],
    hubs=[]  # For spoke mode: [{"hubId": "N_HQ001", "useDefaultRoute": True}]
)
```

**Available VLAN Types:**
- `corporate` - VLAN 10, DHCP enabled
- `guest` - VLAN 20, DHCP enabled
- `voice` - VLAN 30, DHCP enabled
- `iot` - VLAN 40, DHCP enabled
- `management` - VLAN 99, No DHCP
- `server` - VLAN 50, No DHCP

### 2. DeviceGenerator (`device_generator.py`)

Generates Meraki devices with realistic serial numbers, MAC addresses, and firmware versions.

```python
from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS

gen = DeviceGenerator(seed=42)

# Generate single device
device = gen.generate_device(
    network_id="N_HQ001",
    organization_id="883652",
    product_type="wireless",  # appliance, switch, wireless, cellularGateway
    model="MR57",
    name="HQ-AP-01",
    location=US_LOCATIONS[0],  # San Francisco
    network_octet=10,
    device_index=0,
    tags=["wireless-ap", "indoor", "wifi6e"]
)

# Generate device availability
availability = gen.generate_device_availability(device)

# Generate all devices for a network
devices, availabilities = gen.generate_devices_for_network(
    network_id="N_HQ001",
    organization_id="883652",
    location=US_LOCATIONS[0],
    config={
        "appliances": [{"model": "MX450", "name": "HQ-MX-01", "tags": ["hub"]}],
        "switches": [{"model": "MS425-32", "count": 2, "name_prefix": "HQ-SW", "tags": ["core"]}],
        "wireless": [{"model": "MR57", "count": 10, "name_prefix": "HQ-AP", "tags": ["wifi6e"]}],
        "cellular": [{"model": "MG41", "name": "HQ-MG-01", "tags": ["backup"]}],
    },
    network_octet=10
)
```

**Available Device Models:**

| Type | Models |
|------|--------|
| Appliance | MX450, MX250, MX85, MX75, MX68, MX68W, MX67, MX67C |
| Switch | MS425-32, MS350-48, MS250-48, MS225-48, MS225-24, MS120-24, MS120-8 |
| Wireless | MR57, MR56, MR46, MR36, MR33, MR30H |
| Cellular | MG41, MG21 |
| Sensor | MT10, MT12, MT14 |
| Camera | MV12W, MV22, MV72 |

**US Locations Available:**
San Francisco, New York, Chicago, Los Angeles, Seattle, Austin, Denver, Boston, Atlanta, Miami, Dallas, Phoenix, Portland, Minneapolis, Detroit, Philadelphia, San Diego, Houston, Charlotte, Salt Lake City

### 3. ClientGenerator (`client_generator.py`)

Generates network clients with realistic manufacturers, device types, and usage patterns.

```python
from seed_data.generators.client_generator import ClientGenerator

gen = ClientGenerator(seed=42)

# Generate network client (full format for /networks/{id}/clients)
network_client = gen.generate_network_client(
    client_id="k123456",
    network_id="N_HQ001",
    vlan_id=10,
    client_index=0
)

# Generate device client (simplified format for /devices/{serial}/clients)
device_client = gen.generate_device_client(
    client_id="k123456",
    network_id="N_HQ001",
    vlan_id=10,
    client_index=0,
    device_serial="Q2XX-XXXX-XXXX"
)

# Generate clients for entire network
network_clients, device_clients = gen.generate_clients_for_network(
    network_id="N_HQ001",
    vlans=vlans,  # List of VLAN configs
    count=200,    # Number of clients
    devices=devices  # List of devices (clients connect to switches/APs)
)
```

**Client Manufacturers & deviceTypePrediction:**

The `manufacturer` field contains clean vendor names (matching real Meraki API), while `deviceTypePrediction` contains device details:

| Manufacturer | deviceTypePrediction Examples |
|--------------|-------------------------------|
| Apple | "iPhone, iOS 17", "MacBook Pro, macOS Ventura", "iPad, iOS 16" |
| Samsung | "Samsung Galaxy, Android 14", "Samsung Smart TV, Tizen OS" |
| Dell | "Dell Laptop, Windows 11", "Dell Desktop, Windows 10" |
| HP | "HP Laptop, Windows 11", "HP LaserJet Printer", "HP OfficeJet MFP" |
| Lenovo | "Lenovo ThinkPad, Windows 11", "Lenovo ThinkPad, Chrome OS" |
| Google | "Google Pixel, Android 14", "Chromebook, Chrome OS" |
| Cisco | "Cisco IP Phone", "Cisco IP Phone 8845" |
| Zebra | "Zebra Scanner", "Zebra TC52" |
| LG | "LG Smart TV, webOS" |
| Canon/Epson | "Canon Printer", "Epson Printer" |
| GE | "GE Patient Monitor", "GE CARESCAPE Monitor" |
| Philips | "Philips IntelliVue", "Philips Patient Monitor" |
| Axis | "Axis IP Camera", "Axis P3245-V" |

Note: Device type is determined by OUI (first 3 bytes of MAC), not manufacturer name. The same manufacturer (e.g., HP) can have different OUIs for different product lines (laptops vs printers).

## Creating a New Topology

### Step 1: Create Topology File

Create a new file in `seed_data/topologies/`:

```python
# seed_data/topologies/my_topology.py
"""
My Custom Topology

Description of what this topology represents.
"""

from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator


def generate_my_topology(seed: int = 42) -> dict:
    """Generate custom topology data."""
    device_gen = DeviceGenerator(seed=seed)
    client_gen = ClientGenerator(seed=seed)
    network_gen = NetworkGenerator(seed=seed)

    # Initialize result containers
    organizations = []
    networks = []
    devices = []
    device_availabilities = []
    vlans = []
    vlan_profiles = []
    network_clients = []
    device_clients = {}
    vpn_configs = []
    cellular_subnet_pools = []

    # ========================================
    # 1. Create Organization
    # ========================================
    org_id = "123456"
    org = network_gen.generate_organization(
        org_id=org_id,
        name="My Company",
        region="North America"
    )
    organizations.append(org)

    # ========================================
    # 2. Create Networks
    # ========================================
    location = US_LOCATIONS[0]  # San Francisco
    network_id = "N_MAIN001"

    network = network_gen.generate_network(
        network_id=network_id,
        organization_id=org_id,
        name="Main-Office",
        product_types=["appliance", "switch", "wireless"],
        timezone=location["tz"],
        tags=["main", "office"],
        notes="Main office network"
    )
    networks.append(network)

    # ========================================
    # 3. Create Devices
    # ========================================
    device_config = {
        "appliances": [{"model": "MX85", "name": "Main-MX-01", "tags": ["firewall"]}],
        "switches": [{"model": "MS225-48", "count": 2, "name_prefix": "Main-SW", "tags": ["switch"]}],
        "wireless": [{"model": "MR46", "count": 5, "name_prefix": "Main-AP", "tags": ["wifi"]}],
    }

    net_devices, net_avails = device_gen.generate_devices_for_network(
        network_id=network_id,
        organization_id=org_id,
        location=location,
        config=device_config,
        network_octet=10
    )
    devices.extend(net_devices)
    device_availabilities.extend(net_avails)

    # ========================================
    # 4. Create VLANs
    # ========================================
    net_vlans = network_gen.generate_vlans_for_network(
        network_id=network_id,
        vlan_types=["corporate", "guest", "voice"],
        base_third_octet=10
    )
    vlans.extend(net_vlans)

    # ========================================
    # 5. Create VPN Config (optional)
    # ========================================
    vpn_subnets = [
        network_gen.generate_vpn_subnet(vlan["subnet"], use_vpn=True)
        for vlan in net_vlans
    ]
    vpn = network_gen.generate_vpn_config(
        network_id=network_id,
        mode="hub",
        subnets=vpn_subnets
    )
    vpn_configs.append({"network_id": network_id, "config": vpn})

    # ========================================
    # 6. Create Clients
    # ========================================
    net_clients, dev_clients = client_gen.generate_clients_for_network(
        network_id=network_id,
        vlans=net_vlans,
        count=100,  # Number of clients
        devices=net_devices
    )
    network_clients.extend(net_clients)
    device_clients.update(dev_clients)

    # ========================================
    # Return Complete Topology
    # ========================================
    return {
        "topology_name": "my_topology",
        "description": "My custom topology description",
        "organizations": organizations,
        "networks": networks,
        "devices": devices,
        "device_availabilities": device_availabilities,
        "vlans": vlans,
        "vlan_profiles": vlan_profiles,
        "network_clients": network_clients,
        "device_clients": device_clients,
        "vpn_configs": vpn_configs,
        "cellular_subnet_pools": cellular_subnet_pools,
        "stats": {
            "organizations": len(organizations),
            "networks": len(networks),
            "devices": len(devices),
            "vlans": len(vlans),
            "clients": len(network_clients),
        }
    }
```

### Step 2: Register Topology in Seed Script

Edit `seed_data/seed_dynamodb.py`:

```python
# Add import at top
from seed_data.topologies.my_topology import generate_my_topology

# Add to main() function
if args.topology in ["my_topology", "all"]:
    print("\nGenerating my topology...")
    topologies_to_seed.append(generate_my_topology())
```

### Step 3: Seed the Topology

```bash
# Seed to AWS DynamoDB
python seed_data/seed_dynamodb.py \
    --profile okta-sso \
    --region eu-west-1 \
    --topology my_topology

# Seed to local DynamoDB
python seed_data/seed_dynamodb.py \
    --local \
    --topology my_topology
```

## Seeding Commands

### Full Seed (All Topologies)

```bash
# AWS
python seed_data/seed_dynamodb.py \
    --profile okta-sso \
    --region eu-west-1 \
    --topology all

# Local
python seed_data/seed_dynamodb.py --local --topology all
```

### Single Topology

```bash
python seed_data/seed_dynamodb.py \
    --profile okta-sso \
    --region eu-west-1 \
    --topology hub_spoke
```

### Custom Table Names

```bash
python seed_data/seed_dynamodb.py \
    --profile okta-sso \
    --region eu-west-1 \
    --config-table MerakiMock_Config_dev \
    --data-table MerakiMock_Data_dev \
    --topology hub_spoke
```

### Set Default Active Topology

```bash
python seed_data/seed_dynamodb.py \
    --profile okta-sso \
    --region eu-west-1 \
    --topology all \
    --default-topology mesh
```

## DynamoDB Data Model

### Config Table (`MerakiMock_Config`)

| PK | SK | Description |
|----|-----|-------------|
| `CONFIG` | `ACTIVE_TOPOLOGY` | Currently active topology |
| `TOPOLOGY` | `{topology_name}` | Registered topology metadata |

### Data Table (`MerakiMock_Data`)

| PK | SK | GSI1PK | GSI1SK |
|----|-----|--------|--------|
| `{topology}#organization` | `{org_id}` | - | - |
| `{topology}#network` | `{network_id}` | `{topology}#organization#{org_id}` | `network#{network_id}` |
| `{topology}#device` | `{serial}` | `{topology}#organization#{org_id}` | `device#{serial}` |
| `{topology}#vlan` | `{network_id}#{vlan_id}` | `{topology}#network#{network_id}` | `vlan#{vlan_id}` |
| `{topology}#network_client` | `{client_id}` | `{topology}#network#{network_id}` | `network_client#{client_id}` |
| `{topology}#client` | `{serial}#{client_id}` | `{topology}#device#{serial}` | `client#{client_id}` |

## Meraki API Field Reference

### Network Fields (all included)
```json
{
  "id": "N_24329156",
  "organizationId": "2930418",
  "name": "Main Office",
  "productTypes": ["appliance", "switch", "wireless"],
  "timeZone": "America/Los_Angeles",
  "tags": ["tag1", "tag2"],
  "enrollmentString": null,
  "url": "https://...",
  "notes": "Description",
  "details": null,
  "isBoundToConfigTemplate": false,
  "isVirtual": false
}
```

### Device Fields (all included)
```json
{
  "serial": "Q2XX-XXXX-XXXX",
  "name": "My AP",
  "mac": "00:18:0A:XX:XX:XX",
  "networkId": "N_24329156",
  "organizationId": "2930418",
  "model": "MR57",
  "productType": "wireless",
  "firmware": "MR 30.5",
  "lanIp": "10.0.0.1",
  "tags": ["tag1"],
  "lat": 37.7749,
  "lng": -122.4194,
  "address": "123 Main St",
  "notes": null,
  "details": [],
  "imei": "123456789000000"  // cellular only
}
```

### Client Fields (network clients)
```json
{
  "id": "k74272e",
  "mac": "22:33:44:55:66:77",
  "ip": "192.168.10.5",
  "ip6": null,
  "ip6Local": null,
  "description": "GALAXY-M03A",
  "firstSeen": 1518365681,
  "lastSeen": 1526087474,
  "manufacturer": "Samsung",
  "os": "Android 13",
  "deviceTypePrediction": "Samsung Galaxy, Android 13",
  "user": "john.smith",
  "vlan": "10",
  "namedVlan": "VLAN_10",
  "ssid": "Corporate",
  "switchport": null,
  "status": "Online",
  "recentDeviceConnection": "Wireless",
  "recentDeviceSerial": "Q2XX-XXXX-XXXX",
  "wirelessCapabilities": "802.11ax - 5 GHz",
  "smInstalled": false,
  "notes": null,
  "usage": {"sent": 138000, "recv": 61000}
}
```

## Correlation Chain

InfoBlox and other consumers should follow this chain to get full location data:

```
CLIENT                      DEVICE                    NETWORK                ORGANIZATION
─────────────────────────────────────────────────────────────────────────────────────────
recentDeviceSerial    ───►  serial
                            networkId           ───►  id
                            lat, lng, address         name (SITE)
                                                      timeZone (REGION HINT)
                                                      organizationId    ───►  id
                                                                              cloud.region.name
                                                                              cloud.region.host.name
```

## Troubleshooting

### Old Data Not Replaced
Client IDs are randomly generated. Delete old data before re-seeding:

```python
# Delete topology data
import boto3
session = boto3.Session(profile_name='okta-sso')
client = session.client('dynamodb', region_name='eu-west-1')

# Query and delete all items with PK starting with 'hub_spoke#'
# (See seed_dynamodb.py for full implementation)
```

### Verify Data Format
```bash
./venv/bin/python -c "
from seed_data.generators.client_generator import ClientGenerator
gen = ClientGenerator(seed=42)
client = gen.generate_network_client('test', 'N_TEST', 10, 0)
print(client)
"
```
