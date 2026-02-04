# Mock Meraki Dashboard API

A fully-functional mock implementation of the Cisco Meraki Dashboard API, designed for **Infoblox Universal DDI** integration testing and demos.

## Overview

This project provides a serverless mock Meraki API that returns realistic network infrastructure data including organizations, networks, devices, VLANs, and clients. Perfect for:

- **Infoblox Universal DDI Portal** testing with Third Party IPAM providers
- Demo environments without requiring real Meraki infrastructure
- Development and integration testing
- Training and educational purposes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Infrastructure                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Route 53 ──► CloudFront ──► API Gateway ──► Lambda ──► DynamoDB │
│     │              │              │                              │
│     │              │              └── WAF Protection             │
│     │              └── TLS 1.2 + Custom Domain                   │
│     └── Custom Domain                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Live Demo

**Want to try the API?** Contact **Igor Racic** for API access credentials.

The hosted API includes:
- Custom domain with SSL
- WAF protection (rate limiting, OWASP rules)
- Pre-seeded realistic enterprise data

## API Endpoints

All endpoints match the official [Meraki Dashboard API v1](https://developer.cisco.com/meraki/api-v1/) specification:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/organizations` | List all organizations |
| `GET /api/v1/organizations/{orgId}/networks` | List networks |
| `GET /api/v1/organizations/{orgId}/devices` | List all devices |
| `GET /api/v1/organizations/{orgId}/devices/availabilities` | Device status |
| `GET /api/v1/networks/{networkId}/clients` | List network clients |
| `GET /api/v1/networks/{networkId}/appliance/vlans` | List VLANs |
| `GET /api/v1/devices/{serial}/clients` | List device clients |

## Seeded Topology

The default **hub-spoke** topology simulates a realistic enterprise network:

### Organization
| Field | Value |
|-------|-------|
| Name | Acme Corporation |
| ID | 883652 |
| Region | North America |

### Networks (21 total)

| Type | Count | Examples |
|------|-------|----------|
| HQ Campus | 1 | Hub site with full infrastructure |
| Branch Offices | 15 | NYC, Chicago, LA, Seattle, Austin, Denver, Boston, Atlanta, Miami, Dallas, Phoenix, Portland, Minneapolis, Detroit, Philadelphia |
| Remote Sites | 5 | Cellular-connected locations |

### Devices (134 total)

| Device Type | Models | Tags |
|-------------|--------|------|
| Security Appliances | MX450, MX250, MX85, MX68, MX67 | `security-appliance`, `hub`/`spoke` |
| Switches | MS425-32, MS350-48, MS225-48, MS120-24 | `switch`, `core-layer`, `distribution-layer`, `access-layer` |
| Wireless APs | MR57, MR56, MR46, MR36, MR33 | `wireless-ap`, `indoor`, `wifi6e` |
| Cellular Gateways | MG41, MG21 | `cellular-gateway`, `wan-backup` |

### VLANs per Network

| VLAN ID | Name | Subnet Example | Purpose |
|---------|------|----------------|---------|
| 10 | Corporate | 192.168.x.0/24 | Employee workstations |
| 20 | Guest | 192.168.x.0/24 | Guest WiFi |
| 30 | Voice | 192.168.x.0/24 | VoIP phones |
| 40 | IoT | 192.168.x.0/24 | Sensors and IoT devices |
| 50 | Servers | 192.168.x.0/24 | Data center servers |
| 99 | Management | 192.168.x.0/24 | Network management |

### Clients (739 total)

Realistic client devices with proper `deviceTypePrediction` format matching Meraki API:

| Manufacturer | Device Type Predictions |
|--------------|------------------------|
| Apple | `iPhone, iOS 17`, `MacBook Pro, macOS Ventura`, `iPad, iOS 16` |
| Samsung | `Samsung Galaxy, Android 14`, `Samsung Tablet, Android 13` |
| Dell | `Dell Laptop, Windows 11`, `Dell Desktop, Windows 10` |
| Lenovo | `Lenovo ThinkPad, Windows 11` |
| Cisco | `Cisco IP Phone` |
| HP/Canon/Epson | `HP Printer`, `Canon Printer` |
| IoT Device | `IoT Sensor`, `IP Camera` |

## Data Generation

### Generators

```
seed_data/generators/
├── device_generator.py    # Devices & availabilities
├── client_generator.py    # Network & device clients
├── network_generator.py   # Orgs, networks, VLANs, VPN
```

### Creating Custom Topologies

1. Create a topology file in `seed_data/topologies/`:

```python
# seed_data/topologies/my_topology.py
from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator

def generate_my_topology(seed: int = 42) -> dict:
    device_gen = DeviceGenerator(seed=seed)
    client_gen = ClientGenerator(seed=seed)
    network_gen = NetworkGenerator(seed=seed)

    # Create organization
    org = network_gen.generate_organization("123456", "My Company", "North America")

    # Create network
    network = network_gen.generate_network(
        network_id="N_001",
        organization_id="123456",
        name="Main-Office",
        product_types=["appliance", "switch", "wireless"],
        timezone="America/New_York",
        tags=["main", "office"]
    )

    # Create VLANs
    vlans = network_gen.generate_vlans_for_network(
        network_id="N_001",
        vlan_types=["corporate", "guest", "voice"],
        base_third_octet=100
    )

    # Create devices
    devices, availabilities = device_gen.generate_devices_for_network(
        network_id="N_001",
        organization_id="123456",
        location=US_LOCATIONS[0],
        config={
            "appliances": [{"model": "MX85", "name": "Main-MX"}],
            "switches": [{"model": "MS225-48", "count": 2, "name_prefix": "SW"}],
            "wireless": [{"model": "MR46", "count": 5, "name_prefix": "AP"}],
        },
        network_octet=100
    )

    # Create clients
    clients, device_clients = client_gen.generate_clients_for_network(
        network_id="N_001",
        vlans=vlans,
        count=100,
        devices=devices
    )

    return {
        "topology_name": "my_topology",
        "organizations": [org],
        "networks": [network],
        "devices": devices,
        "device_availabilities": availabilities,
        "vlans": vlans,
        "network_clients": clients,
        "device_clients": device_clients,
        # ... other fields
    }
```

2. Seed to DynamoDB:

```bash
python seed_data/seed_dynamodb.py \
    --profile your-aws-profile \
    --region eu-west-1 \
    --topology my_topology
```

### Available Topologies

| Topology | Orgs | Networks | Devices | Clients | Description |
|----------|------|----------|---------|---------|-------------|
| `hub_spoke` | 1 | 21 | 134 | 740 | Enterprise with HQ + branches |
| `mesh` | 1 | 8 | 150+ | 1500+ | Data center mesh |
| `multi_org` | 5 | 20 | 200+ | 2000+ | MSP multi-tenant |

## Self-Hosting

### Prerequisites

- AWS Account
- AWS SAM CLI
- Python 3.11+
- Docker (for local testing)

### Deploy to AWS

```bash
# Build
sam build

# Deploy
sam deploy --guided --profile your-profile --region eu-west-1
```

### Seed Data

```bash
python seed_data/seed_dynamodb.py \
    --profile your-profile \
    --region eu-west-1 \
    --topology hub_spoke
```

### Set Up Custom Domain (Optional)

1. Request ACM certificate for your domain
2. Create API Gateway custom domain
3. Create Route 53 alias record
4. (Optional) Add WAF for protection

## API Response Examples

### Network Client
```json
{
  "id": "k437944",
  "mac": "22:33:44:55:66:77",
  "ip": "192.168.100.5",
  "description": "GALAXY-M03A",
  "manufacturer": "Samsung",
  "os": "Android 13",
  "deviceTypePrediction": "Samsung Galaxy, Android 13",
  "firstSeen": 1768239666,
  "lastSeen": 1770224526,
  "status": "Online",
  "vlan": "10",
  "namedVlan": "VLAN_10",
  "recentDeviceSerial": "Q2XX-XXXX-XXXX",
  "recentDeviceConnection": "Wireless",
  "usage": { "sent": 138000, "recv": 61000 }
}
```

### Device
```json
{
  "serial": "Q2E0-CCG3-B103",
  "name": "Branch-NYC-AP-01",
  "model": "MR57",
  "productType": "wireless",
  "mac": "00:18:0A:XX:XX:XX",
  "networkId": "N_BR001",
  "lanIp": "192.168.100.5",
  "firmware": "MR 30.5",
  "tags": ["wireless-ap", "indoor", "wifi6e"],
  "lat": 40.7128,
  "lng": -74.0060,
  "address": "123 NYC St",
  "details": [],
  "notes": null
}
```

### VLAN
```json
{
  "id": "10",
  "interfaceId": "6022768040250",
  "networkId": "N_BR001",
  "name": "Corporate",
  "subnet": "192.168.100.0/24",
  "applianceIp": "192.168.100.1",
  "dhcpHandling": "Run a DHCP server",
  "dhcpLeaseTime": "1 day",
  "dnsNameservers": "upstream_dns"
}
```

## Infoblox Integration

1. Get API endpoint and key (contact Igor or deploy your own)
2. In Infoblox Portal: **Configure → Networking → Third Party IPAM Providers → Meraki**
3. Enter the API URL and key
4. Run sync/discovery
5. View assets in **Monitor → Assets → Asset Inventory**

### What Infoblox Sees

| Data Type | Count |
|-----------|-------|
| Networks (IP Spaces) | 56 |
| Assets (Devices + Clients) | 873 |
| Subnets with utilization | Client IPs per VLAN |

## Meraki API Compliance

All responses match official Meraki API v1 specification:

| Field | Format |
|-------|--------|
| `deviceTypePrediction` | `"iPhone SE, iOS9.3.5"` format |
| `firstSeen` / `lastSeen` | Unix timestamp (integer) |
| `network` (availability) | `{"id": "N_XXX"}` object format |
| `details` | Array of name/value pairs |
| Client IPs | Match VLAN subnet ranges |

## Project Structure

```
.
├── src/
│   ├── handlers/           # Lambda handlers
│   ├── middleware/         # API key auth
│   └── utils/              # DynamoDB client
├── seed_data/
│   ├── generators/         # Data generators
│   ├── topologies/         # Network topologies
│   └── seed_dynamodb.py    # Seeding script
├── docs/
│   ├── TOPOLOGY_GUIDE.md   # Contributing & self-hosting guide
│   └── DATA_GENERATION.md  # Detailed docs
├── template.yaml           # SAM template
├── CONTRIBUTING.md         # Quick contribution guide
└── README.md
```

## Contributing

Want to add a new topology? See [CONTRIBUTING.md](CONTRIBUTING.md) or the full [Topology Guide](docs/TOPOLOGY_GUIDE.md).

## Security Notes

- API Key authentication (supports both `X-Cisco-Meraki-API-Key` and `Authorization: Bearer`)
- WAF protection available (rate limiting, OWASP rules)
- TLS 1.2 minimum
- No real credentials in responses

## License

MIT License - Feel free to use for testing and demos.

## Contact

**Igor Racic** - For API access or questions

---

*This is a mock API for testing purposes. It is not affiliated with or endorsed by Cisco Meraki or Infoblox.*
