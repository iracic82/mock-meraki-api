"""
Mesh VPN Topology Generator

Generates a regional data center topology with:
- 1 Organization ("Global DataCorp")
- 8 Networks (data centers in full mesh VPN)
- 150+ Devices across all DCs
- 1500+ Clients distributed across the network
- Full mesh site-to-site VPN configuration
"""

from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator


# Data center configurations
DC_CONFIGS = [
    {"name": "DC-Primary-East", "location_idx": 1, "tier": "primary"},   # NYC
    {"name": "DC-Primary-West", "location_idx": 0, "tier": "primary"},   # San Francisco
    {"name": "DC-Secondary-Central", "location_idx": 2, "tier": "secondary"},  # Chicago
    {"name": "DC-Secondary-South", "location_idx": 5, "tier": "secondary"},    # Austin
    {"name": "DC-Edge-Northwest", "location_idx": 4, "tier": "edge"},    # Seattle
    {"name": "DC-Edge-Southwest", "location_idx": 3, "tier": "edge"},    # LA
    {"name": "DC-Edge-Northeast", "location_idx": 7, "tier": "edge"},    # Boston
    {"name": "DC-Edge-Southeast", "location_idx": 9, "tier": "edge"},    # Miami
]


def generate_mesh_topology(seed: int = 43) -> dict:
    """
    Generate complete mesh VPN topology data.

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

    # ====================================
    # Organization
    # ====================================
    org_id = "994763"
    org = network_gen.generate_organization(
        org_id=org_id,
        name="Global DataCorp",
        region="North America"
    )
    organizations.append(org)

    # ====================================
    # Data Center Networks (Full Mesh)
    # ====================================
    network_ids = []

    for i, dc_config in enumerate(DC_CONFIGS):
        location = US_LOCATIONS[dc_config["location_idx"]]
        network_id = f"N_DC{i + 1:03d}"
        network_ids.append(network_id)

        # Determine device counts based on tier
        tier = dc_config["tier"]
        if tier == "primary":
            device_counts = {
                "mx_count": 2,  # HA pair
                "core_sw_count": 4,
                "dist_sw_count": 8,
                "acc_sw_count": 16,
                "ap_count": 30,
                "mg_count": 2,
                "client_count": 300,
            }
        elif tier == "secondary":
            device_counts = {
                "mx_count": 2,
                "core_sw_count": 2,
                "dist_sw_count": 4,
                "acc_sw_count": 8,
                "ap_count": 15,
                "mg_count": 1,
                "client_count": 180,
            }
        else:  # edge
            device_counts = {
                "mx_count": 1,
                "core_sw_count": 1,
                "dist_sw_count": 2,
                "acc_sw_count": 4,
                "ap_count": 8,
                "mg_count": 1,
                "client_count": 100,
            }

        # Create network
        dc_network = network_gen.generate_network(
            network_id=network_id,
            organization_id=org_id,
            name=dc_config["name"],
            product_types=["appliance", "switch", "wireless", "cellularGateway"],
            timezone=location["tz"],
            tags=["datacenter", tier, f"region-{location['state']}"],
            notes=f"{tier.capitalize()} data center in {location['city']}, {location['state']}"
        )
        networks.append(dc_network)

        # Device configuration
        dev_config = {
            "appliances": [
                {"model": "MX450", "name": f"{dc_config['name']}-MX-{j + 1:02d}"}
                for j in range(device_counts["mx_count"])
            ],
            "switches": [
                {"model": "MS425-32", "count": device_counts["core_sw_count"], "name_prefix": f"{dc_config['name']}-CORE", "tags": ["core"]},
                {"model": "MS350-48", "count": device_counts["dist_sw_count"], "name_prefix": f"{dc_config['name']}-DIST", "tags": ["distribution"]},
                {"model": "MS250-48", "count": device_counts["acc_sw_count"], "name_prefix": f"{dc_config['name']}-ACC", "tags": ["access"]},
            ],
            "wireless": [
                {"model": "MR57", "count": device_counts["ap_count"], "name_prefix": f"{dc_config['name']}-AP", "tags": ["warehouse"]},
            ],
            "cellular": [
                {"model": "MG41", "name": f"{dc_config['name']}-MG-{j + 1:02d}"}
                for j in range(device_counts["mg_count"])
            ],
        }

        # Generate devices
        dc_devices, dc_availabilities = device_gen.generate_devices_for_network(
            network_id=network_id,
            organization_id=org_id,
            location=location,
            config=dev_config,
            network_octet=10 + i * 10
        )
        devices.extend(dc_devices)
        device_availabilities.extend(dc_availabilities)

        # VLANs - data center specific
        dc_vlans = network_gen.generate_vlans_for_network(
            network_id=network_id,
            vlan_types=["corporate", "server", "management", "voice", "iot", "guest"],
            base_third_octet=i * 20
        )
        vlans.extend(dc_vlans)

        # VLAN Profiles
        dc_profile = network_gen.generate_vlan_profile(
            network_id=network_id,
            profile_id=f"dc-{tier}",
            name=f"DC {tier.capitalize()} Profile",
            vlan_names=["Servers", "Management", "Corporate"],
            is_default=True
        )
        vlan_profiles.append(dc_profile)

        # Cellular subnet pool
        cellular_pool = network_gen.generate_cellular_subnet_pool(
            network_id=network_id,
            cidr=f"10.{220 + i}.0.0",
            mask=16
        )
        cellular_subnet_pools.append({"network_id": network_id, "config": cellular_pool})

        # Clients
        dc_net_clients, dc_dev_clients = client_gen.generate_clients_for_network(
            network_id=network_id,
            vlans=dc_vlans,
            count=device_counts["client_count"],
            devices=dc_devices
        )
        network_clients.extend(dc_net_clients)
        device_clients.update(dc_dev_clients)

    # ====================================
    # VPN Configs (Full Mesh)
    # ====================================
    for i, network_id in enumerate(network_ids):
        # Get VLANs for this network
        net_vlans = [v for v in vlans if v["networkId"] == network_id]
        vpn_subnets = [
            network_gen.generate_vpn_subnet(vlan["subnet"], use_vpn=True)
            for vlan in net_vlans
        ]

        # In full mesh, every site is a hub that peers with all other sites
        # Each site has all other sites as hubs
        other_network_ids = [nid for nid in network_ids if nid != network_id]

        # Primary DCs are true hubs, others are spokes connecting to primaries
        tier = DC_CONFIGS[i]["tier"]

        if tier == "primary":
            vpn_config = network_gen.generate_vpn_config(
                network_id=network_id,
                mode="hub",
                subnets=vpn_subnets
            )
        else:
            # Connect to both primary DCs
            primary_hubs = [
                {"hubId": nid, "useDefaultRoute": False}
                for j, nid in enumerate(network_ids)
                if DC_CONFIGS[j]["tier"] == "primary"
            ]
            vpn_config = network_gen.generate_vpn_config(
                network_id=network_id,
                mode="spoke",
                subnets=vpn_subnets,
                hubs=primary_hubs
            )

        vpn_configs.append({"network_id": network_id, "config": vpn_config})

    # ====================================
    # Return complete topology
    # ====================================
    return {
        "topology_name": "mesh",
        "description": "Regional data center mesh VPN topology with primary/secondary/edge tiers",
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
