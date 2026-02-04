# Contributing Topologies

This guide explains how to contribute new network topologies to the Mock Meraki API project.

## Important: Self-Hosting Model

**This is a self-hosting project.** Community topologies are NOT deployed to the hosted demo instance (`meraki-api.highvelocitynetworking.com`). That instance is maintained separately for Infoblox integration demos.

When you contribute a topology:
1. Your topology is added to the repository
2. Anyone (including you) can deploy it to their **own AWS account**
3. The hosted demo instance remains unchanged

## Quick Start

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/Meraki_Controller_API.git
cd Meraki_Controller_API
pip install -r requirements.txt
```

### 2. Create Your Topology

Create a new file in `seed_data/topologies/`:

```python
# seed_data/topologies/my_topology.py

from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator


def generate_my_topology_topology(seed: int = 42) -> dict:
    """
    Generate a custom topology.

    IMPORTANT: Function name MUST be: generate_{filename}_topology
    For my_topology.py -> generate_my_topology_topology()
    """
    device_gen = DeviceGenerator(seed=seed)
    client_gen = ClientGenerator(seed=seed)
    network_gen = NetworkGenerator(seed=seed)

    # Create organization
    org = network_gen.generate_organization(
        org_id="123456",
        name="My Company",
        region="North America"
    )

    # Create networks
    networks = []
    devices = []
    vlans = []
    clients = []
    device_clients = {}
    availabilities = []

    # Example: Create a simple office network
    network = network_gen.generate_network(
        network_id="N_001",
        organization_id="123456",
        name="Main-Office",
        product_types=["appliance", "switch", "wireless"],
        timezone="America/New_York",
        tags=["office", "main"]
    )
    networks.append(network)

    # Create VLANs for the network
    network_vlans = network_gen.generate_vlans_for_network(
        network_id="N_001",
        vlan_types=["corporate", "guest", "voice", "iot"],
        base_third_octet=100
    )
    vlans.extend(network_vlans)

    # Create devices
    location = US_LOCATIONS[0]  # New York
    net_devices, net_avail = device_gen.generate_devices_for_network(
        network_id="N_001",
        organization_id="123456",
        location=location,
        config={
            "appliances": [{"model": "MX85", "name": "Main-MX"}],
            "switches": [{"model": "MS225-48", "count": 2, "name_prefix": "SW"}],
            "wireless": [{"model": "MR46", "count": 5, "name_prefix": "AP"}],
        },
        network_octet=100
    )
    devices.extend(net_devices)
    availabilities.extend(net_avail)

    # Create clients
    net_clients, dev_clients = client_gen.generate_clients_for_network(
        network_id="N_001",
        vlans=network_vlans,
        count=100,
        devices=net_devices
    )
    clients.extend(net_clients)
    device_clients.update(dev_clients)

    # Return the complete topology
    return {
        "topology_name": "my_topology",
        "organizations": [org],
        "networks": networks,
        "devices": devices,
        "device_availabilities": availabilities,
        "vlans": vlans,
        "network_clients": clients,
        "device_clients": device_clients,
        "vpn_configs": [],
        "stats": {
            "organizations": 1,
            "networks": len(networks),
            "devices": len(devices),
            "vlans": len(vlans),
            "clients": len(clients),
        }
    }
```

### 3. Validate Locally

```bash
# Run the validation script
python scripts/validate_topologies.py

# You should see:
# === Validating my_topology topology ===
#   Organizations: 1
#   Networks: 1
#   Devices: 8
#   VLANs: 4
#   Clients: 100
#   ✓ Topology "my_topology" is valid
```

### 4. Submit PR

```bash
git checkout -b add-my-topology
git add seed_data/topologies/my_topology.py
git commit -m "Add my_topology: description of your topology"
git push origin add-my-topology
```

Then open a Pull Request. CI will automatically validate your topology.

---

## Self-Hosting Guide

Want to run your own Mock Meraki API? Follow this guide to deploy to your AWS account.

### Prerequisites

| Requirement | Installation |
|-------------|--------------|
| AWS Account | [Sign up](https://aws.amazon.com/) |
| AWS CLI | `brew install awscli` or [AWS docs](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) |
| AWS SAM CLI | `brew install aws-sam-cli` or [SAM docs](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) |
| Python 3.11+ | `brew install python@3.11` |
| Docker | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local testing) |

Configure AWS credentials:
```bash
aws configure --profile my-profile
# Enter your AWS Access Key ID, Secret, and preferred region
```

### What Gets Deployed

The SAM template (`template.yaml`) creates these AWS resources:

```
┌─────────────────────────────────────────────────────────────┐
│                    Your AWS Account                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  API Gateway (REST API)                                      │
│  └── /api/v1/* routes                                        │
│                                                              │
│  Lambda Function (Python 3.11)                               │
│  └── Handles all Meraki API endpoints                        │
│                                                              │
│  DynamoDB Tables (On-Demand billing)                         │
│  ├── MerakiMock_Config  (topology config)                    │
│  └── MerakiMock_Data    (all entity data)                    │
│                                                              │
│  IAM Role                                                    │
│  └── Lambda execution role with DynamoDB access              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: Clone and Install

```bash
git clone https://github.com/iracic82/mock-meraki-api.git
cd mock-meraki-api
pip install -r requirements.txt
```

### Step 2: Build

```bash
sam build
```

This packages the Lambda function and dependencies.

### Step 3: Deploy

```bash
sam deploy --guided --profile my-profile --region eu-west-1
```

SAM will prompt you for:
- **Stack Name**: e.g., `mock-meraki-api`
- **AWS Region**: e.g., `eu-west-1`
- **Confirm changes**: Yes
- **Allow IAM role creation**: Yes
- **Save arguments to samconfig.toml**: Yes (for future deploys)

**Note:** `samconfig.toml` contains your deployment settings. It's gitignored to avoid committing profile names.

### Step 4: Get Your API URL

After deployment, SAM outputs your API URL:

```
Outputs
-----------------------------------------
Key                 MerakiMockApiUrl
Description         API Gateway endpoint URL
Value               https://abc123xyz.execute-api.eu-west-1.amazonaws.com/Prod
```

Or retrieve it later:
```bash
aws cloudformation describe-stacks \
    --stack-name mock-meraki-api \
    --profile my-profile \
    --region eu-west-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`MerakiMockApiUrl`].OutputValue' \
    --output text
```

### Step 5: Seed Your Topology

```bash
python seed_data/seed_dynamodb.py \
    --profile my-profile \
    --region eu-west-1 \
    --topology hub_spoke
```

Available topologies: `hub_spoke`, `mesh`, `multi_org`, or your custom topology.

### Step 6: Test Your API

```bash
# Set your API URL
export API_URL="https://abc123xyz.execute-api.eu-west-1.amazonaws.com/Prod"

# Test organizations endpoint
curl -H "X-Cisco-Meraki-API-Key: any-key-works" \
     "$API_URL/api/v1/organizations"

# Test networks
curl -H "X-Cisco-Meraki-API-Key: any-key-works" \
     "$API_URL/api/v1/organizations/883652/networks"

# Test devices
curl -H "X-Cisco-Meraki-API-Key: any-key-works" \
     "$API_URL/api/v1/organizations/883652/devices"
```

### Cost Estimate

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| API Gateway | ~$0.50 (low traffic) |
| Lambda | ~$0.10 (free tier covers most) |
| DynamoDB | ~$1-2 (on-demand, ~10MB data) |
| **Total** | **~$2-3/month** |

*Costs vary based on usage. Free tier covers most development/demo usage.*

### Optional: Custom Domain

To add a custom domain like `api.yourdomain.com`:

1. **Request ACM Certificate** (must be in `us-east-1` for edge-optimized API):
   ```bash
   aws acm request-certificate \
       --domain-name api.yourdomain.com \
       --validation-method DNS \
       --region us-east-1 \
       --profile my-profile
   ```

2. **Add DNS validation record** to your domain

3. **Create API Gateway custom domain** and map to your API

4. **Create Route 53 alias record** pointing to the API Gateway domain

See [AWS docs](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html) for detailed instructions.

### Optional: WAF Protection

For production use, add AWS WAF:

```bash
# Create WAF Web ACL with rate limiting
aws wafv2 create-web-acl \
    --name mock-meraki-waf \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules '[{"Name":"RateLimit","Priority":1,"Statement":{"RateBasedStatement":{"Limit":1000,"AggregateKeyType":"IP"}},"Action":{"Block":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"RateLimit"}}]' \
    --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=MockMerakiWAF \
    --region eu-west-1 \
    --profile my-profile
```

### Cleanup

To delete all resources:

```bash
sam delete --stack-name mock-meraki-api --profile my-profile --region eu-west-1
```

---

### 5. Submit PR (After Testing)

```bash
git checkout -b add-my-topology
git add seed_data/topologies/my_topology.py
git commit -m "Add my_topology: description of your topology"
git push origin add-my-topology
```

Then open a Pull Request. CI will automatically validate your topology.

## Topology Requirements

### Required Fields

Your topology function must return a dict with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `topology_name` | str | Unique identifier (matches filename) |
| `organizations` | list | At least one organization |
| `networks` | list | At least one network |
| `devices` | list | At least one device |
| `vlans` | list | At least one VLAN |
| `network_clients` | list | Network clients (can be empty) |
| `device_clients` | dict | Device to clients mapping |
| `device_availabilities` | list | Device availability records |

### Meraki API Compliance

All entities must include required fields for Meraki API compatibility:

**Organization:**
- `id`, `name`, `url`, `api`, `cloud`

**Network:**
- `id`, `organizationId`, `name`, `productTypes`, `timeZone`, `tags`, `url`, `isBoundToConfigTemplate`

**Device:**
- `serial`, `name`, `model`, `networkId`, `mac`, `productType`, `firmware`, `lanIp`, `tags`, `lat`, `lng`

**VLAN:**
- `id`, `networkId`, `name`, `subnet`, `applianceIp`

**Client:**
- `id`, `mac`, `ip`, `description`, `manufacturer`, `deviceTypePrediction`, `status`

### Naming Convention

- File: `seed_data/topologies/{name}.py`
- Function: `generate_{name}_topology(seed: int = 42) -> dict`
- The `{name}` must match in both places

## Available Generators

### DeviceGenerator

```python
from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS

device_gen = DeviceGenerator(seed=42)

# Generate devices for a network
devices, availabilities = device_gen.generate_devices_for_network(
    network_id="N_001",
    organization_id="123456",
    location=US_LOCATIONS[0],  # (name, lat, lng, timezone)
    config={
        "appliances": [{"model": "MX85", "name": "Edge-MX"}],
        "switches": [{"model": "MS225-48", "count": 3, "name_prefix": "SW"}],
        "wireless": [{"model": "MR46", "count": 10, "name_prefix": "AP"}],
        "cellular": [{"model": "MG41", "count": 1, "name_prefix": "Cell"}],
    },
    network_octet=100  # For IP addressing: 192.168.{octet}.x
)
```

**Available Models:**
- Appliances: MX450, MX250, MX85, MX75, MX68, MX68W, MX67, MX67C
- Switches: MS425-32, MS350-48, MS250-48, MS225-48, MS120-24, MS120-8
- Wireless: MR57, MR56, MR46, MR36, MR33, MR30H
- Cellular: MG41, MG21

### ClientGenerator

```python
from seed_data.generators.client_generator import ClientGenerator

client_gen = ClientGenerator(seed=42)

# Generate clients for a network
clients, device_clients = client_gen.generate_clients_for_network(
    network_id="N_001",
    vlans=vlans,          # List of VLAN dicts
    count=100,            # Number of clients
    devices=devices       # For device-client associations
)
```

### NetworkGenerator

```python
from seed_data.generators.network_generator import NetworkGenerator

network_gen = NetworkGenerator(seed=42)

# Organization
org = network_gen.generate_organization(
    org_id="123456",
    name="Acme Corp",
    region="North America"
)

# Network
network = network_gen.generate_network(
    network_id="N_001",
    organization_id="123456",
    name="HQ-Network",
    product_types=["appliance", "switch", "wireless"],
    timezone="America/Los_Angeles",
    tags=["headquarters", "hub"]
)

# VLANs
vlans = network_gen.generate_vlans_for_network(
    network_id="N_001",
    vlan_types=["corporate", "guest", "voice", "iot", "servers", "management"],
    base_third_octet=100
)

# VPN Config
vpn = network_gen.generate_vpn_config(
    network_id="N_001",
    mode="hub",  # or "spoke"
    hub_network_ids=[]  # for spoke mode
)
```

## Example Topologies

Look at existing topologies for reference:

| Topology | Description | File |
|----------|-------------|------|
| `hub_spoke` | Enterprise with HQ + 20 branches | `seed_data/topologies/hub_spoke.py` |

## CI Validation

When you submit a PR, GitHub Actions will:

1. **Validate topology structure** - Check required fields
2. **Validate Meraki API compliance** - Check entity fields
3. **Run linting** - Check code style
4. **Report statistics** - Show device/client counts

Your PR must pass all checks before merging.

## Questions?

- Open an issue on GitHub
- Contact Igor Racic for questions about the hosted demo instance
