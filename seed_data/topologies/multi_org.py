"""
Multi-Organization Topology Generator

Generates a managed service provider (MSP) topology with:
- 5 Organizations (different customers)
- 4 Networks per org (20 total)
- 200+ Devices across all orgs
- 2000+ Clients total
- Demonstrates multi-tenancy isolation
"""

from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator


# Customer organization configurations
ORG_CONFIGS = [
    {
        "org_id": "100001",
        "name": "TechStart Inc",
        "industry": "Technology Startup",
        "networks": [
            {"name": "TechStart-HQ", "type": "headquarters", "location_idx": 0},
            {"name": "TechStart-Dev", "type": "office", "location_idx": 4},
            {"name": "TechStart-Sales-East", "type": "branch", "location_idx": 1},
            {"name": "TechStart-Sales-West", "type": "branch", "location_idx": 3},
        ]
    },
    {
        "org_id": "100002",
        "name": "HealthPlus Medical",
        "industry": "Healthcare",
        "networks": [
            {"name": "HealthPlus-Hospital", "type": "headquarters", "location_idx": 2},
            {"name": "HealthPlus-Clinic-A", "type": "branch", "location_idx": 8},
            {"name": "HealthPlus-Clinic-B", "type": "branch", "location_idx": 9},
            {"name": "HealthPlus-Admin", "type": "office", "location_idx": 10},
        ]
    },
    {
        "org_id": "100003",
        "name": "RetailMax Stores",
        "industry": "Retail",
        "networks": [
            {"name": "RetailMax-Corporate", "type": "headquarters", "location_idx": 5},
            {"name": "RetailMax-Store-101", "type": "retail", "location_idx": 11},
            {"name": "RetailMax-Store-102", "type": "retail", "location_idx": 12},
            {"name": "RetailMax-Warehouse", "type": "warehouse", "location_idx": 6},
        ]
    },
    {
        "org_id": "100004",
        "name": "EduLearn Academy",
        "industry": "Education",
        "networks": [
            {"name": "EduLearn-Main-Campus", "type": "headquarters", "location_idx": 7},
            {"name": "EduLearn-Library", "type": "office", "location_idx": 7},
            {"name": "EduLearn-Dorms", "type": "residential", "location_idx": 7},
            {"name": "EduLearn-Athletics", "type": "branch", "location_idx": 7},
        ]
    },
    {
        "org_id": "100005",
        "name": "FinanceFirst Bank",
        "industry": "Financial Services",
        "networks": [
            {"name": "FinanceFirst-HQ", "type": "headquarters", "location_idx": 1},
            {"name": "FinanceFirst-Branch-1", "type": "branch", "location_idx": 13},
            {"name": "FinanceFirst-Branch-2", "type": "branch", "location_idx": 14},
            {"name": "FinanceFirst-DC", "type": "datacenter", "location_idx": 15},
        ]
    },
]


# Network type device configurations
NETWORK_TYPE_CONFIGS = {
    "headquarters": {
        "appliances": [{"model": "MX85"}],
        "switches": [
            {"model": "MS350-48", "count": 2},
            {"model": "MS225-48", "count": 4},
        ],
        "wireless": [{"model": "MR56", "count": 12}],
        "clients": 150,
    },
    "office": {
        "appliances": [{"model": "MX68"}],
        "switches": [{"model": "MS225-48", "count": 2}],
        "wireless": [{"model": "MR46", "count": 6}],
        "clients": 60,
    },
    "branch": {
        "appliances": [{"model": "MX67"}],
        "switches": [{"model": "MS120-24", "count": 1}],
        "wireless": [{"model": "MR36", "count": 3}],
        "clients": 30,
    },
    "retail": {
        "appliances": [{"model": "MX68W"}],
        "switches": [{"model": "MS120-8", "count": 1}],
        "wireless": [{"model": "MR33", "count": 4}],
        "clients": 40,
    },
    "warehouse": {
        "appliances": [{"model": "MX75"}],
        "switches": [{"model": "MS225-48", "count": 3}],
        "wireless": [{"model": "MR57", "count": 15}],
        "cellular": [{"model": "MG41"}],
        "clients": 80,
    },
    "residential": {
        "appliances": [{"model": "MX68W"}],
        "switches": [{"model": "MS225-48", "count": 2}],
        "wireless": [{"model": "MR46", "count": 20}],
        "clients": 200,
    },
    "datacenter": {
        "appliances": [{"model": "MX450"}],
        "switches": [
            {"model": "MS425-32", "count": 2},
            {"model": "MS350-48", "count": 4},
        ],
        "wireless": [{"model": "MR57", "count": 4}],
        "cellular": [{"model": "MG41"}],
        "clients": 50,
    },
}


def generate_multi_org_topology(seed: int = 44) -> dict:
    """
    Generate complete multi-organization topology data.

    Args:
        seed: Random seed for reproducibility

    Returns:
        Dictionary with all topology data organized by entity type
    """
    device_gen = DeviceGenerator(seed=seed)
    client_gen = ClientGenerator(seed=seed)
    network_gen = NetworkGenerator(seed=seed)

    # Results storage
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

    # Track network IDs per org for VPN config
    org_network_ids = {}

    network_counter = 0

    for org_config in ORG_CONFIGS:
        org_id = org_config["org_id"]
        org_network_ids[org_id] = []

        # ====================================
        # Organization
        # ====================================
        org = network_gen.generate_organization(
            org_id=org_id,
            name=org_config["name"],
            region="North America"
        )
        organizations.append(org)

        # Find headquarters network for VPN hub
        hq_network_id = None

        # ====================================
        # Networks for this org
        # ====================================
        for net_config in org_config["networks"]:
            network_counter += 1
            location = US_LOCATIONS[net_config["location_idx"] % len(US_LOCATIONS)]
            network_id = f"N_{org_id}_{network_counter:03d}"
            org_network_ids[org_id].append(network_id)

            net_type = net_config["type"]
            type_config = NETWORK_TYPE_CONFIGS.get(net_type, NETWORK_TYPE_CONFIGS["branch"])

            # Track HQ for VPN
            if net_type == "headquarters":
                hq_network_id = network_id

            # Determine product types
            product_types = ["appliance"]
            if type_config.get("switches"):
                product_types.append("switch")
            if type_config.get("wireless"):
                product_types.append("wireless")
            if type_config.get("cellular"):
                product_types.append("cellularGateway")

            # Create network
            network = network_gen.generate_network(
                network_id=network_id,
                organization_id=org_id,
                name=net_config["name"],
                product_types=product_types,
                timezone=location["tz"],
                tags=[org_config["industry"].lower().replace(" ", "-"), net_type],
                notes=f"{org_config['name']} - {net_type} in {location['city']}"
            )
            networks.append(network)

            # Device configuration
            dev_config = {
                "appliances": [
                    {**a, "name": f"{net_config['name']}-MX"}
                    for a in type_config.get("appliances", [])
                ],
                "switches": [
                    {**s, "name_prefix": f"{net_config['name']}-SW"}
                    for s in type_config.get("switches", [])
                ],
                "wireless": [
                    {**w, "name_prefix": f"{net_config['name']}-AP"}
                    for w in type_config.get("wireless", [])
                ],
                "cellular": [
                    {**c, "name": f"{net_config['name']}-MG"}
                    for c in type_config.get("cellular", [])
                ],
            }

            # Generate devices
            net_devices, net_availabilities = device_gen.generate_devices_for_network(
                network_id=network_id,
                organization_id=org_id,
                location=location,
                config=dev_config,
                network_octet=network_counter
            )
            devices.extend(net_devices)
            device_availabilities.extend(net_availabilities)

            # VLANs
            vlan_types = ["corporate", "guest"]
            if net_type in ["headquarters", "datacenter"]:
                vlan_types.extend(["voice", "server", "management"])
            elif net_type == "residential":
                vlan_types = ["corporate", "guest", "iot"]
            elif net_type == "retail":
                vlan_types.extend(["iot"])

            net_vlans = network_gen.generate_vlans_for_network(
                network_id=network_id,
                vlan_types=vlan_types,
                base_third_octet=network_counter * 5
            )
            vlans.extend(net_vlans)

            # Cellular subnet pool
            if type_config.get("cellular"):
                cellular_pool = network_gen.generate_cellular_subnet_pool(
                    network_id=network_id,
                    cidr=f"10.{230 + network_counter}.0.0",
                    mask=16
                )
                cellular_subnet_pools.append({"network_id": network_id, "config": cellular_pool})

            # Clients
            net_net_clients, net_dev_clients = client_gen.generate_clients_for_network(
                network_id=network_id,
                vlans=net_vlans,
                count=type_config["clients"],
                devices=net_devices
            )
            network_clients.extend(net_net_clients)
            device_clients.update(net_dev_clients)

        # ====================================
        # VPN Configs for this org
        # ====================================
        for network_id in org_network_ids[org_id]:
            net_vlans = [v for v in vlans if v["networkId"] == network_id]
            vpn_subnets = [
                network_gen.generate_vpn_subnet(vlan["subnet"], use_vpn=True)
                for vlan in net_vlans
            ]

            if network_id == hq_network_id:
                # HQ is the hub
                vpn_config = network_gen.generate_vpn_config(
                    network_id=network_id,
                    mode="hub",
                    subnets=vpn_subnets
                )
            else:
                # Other sites are spokes
                vpn_config = network_gen.generate_vpn_config(
                    network_id=network_id,
                    mode="spoke",
                    subnets=vpn_subnets,
                    hubs=[{"hubId": hq_network_id, "useDefaultRoute": True}] if hq_network_id else []
                )

            vpn_configs.append({"network_id": network_id, "config": vpn_config})

    # ====================================
    # VLAN Profiles (per org)
    # ====================================
    for org_config in ORG_CONFIGS:
        org_id = org_config["org_id"]
        for network_id in org_network_ids[org_id]:
            profile = network_gen.generate_vlan_profile(
                network_id=network_id,
                profile_id=f"standard-{org_id}",
                name=f"{org_config['name']} Standard",
                vlan_names=["Corporate", "Guest"],
                is_default=True
            )
            vlan_profiles.append(profile)

    # ====================================
    # Return complete topology
    # ====================================
    return {
        "topology_name": "multi_org",
        "description": "Multi-organization MSP topology with 5 customer orgs and 20 total networks",
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
