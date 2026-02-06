"""
Hub-Spoke VPN Topology Generator

Generates a realistic enterprise campus topology with:
- 1 Organization ("Acme Corporation")
- 21 Networks (1 HQ hub + 20 branch spokes)
- 120+ Devices across all sites
- 1200+ Clients distributed across the network
- Full site-to-site VPN configuration
"""

from seed_data.generators.device_generator import DeviceGenerator, US_LOCATIONS
from seed_data.generators.client_generator import ClientGenerator
from seed_data.generators.network_generator import NetworkGenerator


def generate_hub_spoke_topology(seed: int = 42) -> dict:
    """
    Generate complete hub-spoke topology data.

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
    device_statuses = []
    vlans = []
    vlan_profiles = []
    network_clients = []
    device_clients = {}
    vpn_configs = []
    cellular_subnet_pools = []

    # ====================================
    # Organization
    # ====================================
    org_id = "883652"
    org = network_gen.generate_organization(
        org_id=org_id,
        name="Acme Corporation",
        region="North America"
    )
    organizations.append(org)

    # ====================================
    # HQ Network (Hub)
    # ====================================
    hq_location = US_LOCATIONS[0]  # San Francisco
    hq_network_id = "N_HQ001"

    hq_network = network_gen.generate_network(
        network_id=hq_network_id,
        organization_id=org_id,
        name="HQ-Campus",
        product_types=["appliance", "switch", "wireless", "camera", "sensor"],
        timezone=hq_location["tz"],
        tags=["hub", "headquarters", "campus"],
        notes="Corporate headquarters - Hub site for all VPN connections"
    )
    networks.append(hq_network)

    # HQ Devices - larger deployment with infrastructure tags
    hq_device_config = {
        "appliances": [{"model": "MX450", "name": "HQ-MX-01", "tags": ["hub", "security-appliance", "datacenter"]}],
        "switches": [
            {"model": "MS425-32", "count": 2, "name_prefix": "HQ-CORE-SW", "tags": ["switch", "core-layer", "datacenter"]},
            {"model": "MS350-48", "count": 4, "name_prefix": "HQ-DIST-SW", "tags": ["switch", "distribution-layer"]},
            {"model": "MS225-48", "count": 8, "name_prefix": "HQ-ACC-SW", "tags": ["switch", "access-layer"]},
        ],
        "wireless": [
            {"model": "MR57", "count": 20, "name_prefix": "HQ-AP", "tags": ["wireless-ap", "indoor", "wifi6e"]},
        ],
        "cameras": [
            {"model": "MV33", "count": 8, "name_prefix": "HQ-CAM-INDOOR", "tags": ["camera", "indoor", "4k"]},
            {"model": "MV63", "count": 4, "name_prefix": "HQ-CAM-OUTDOOR", "tags": ["camera", "outdoor", "4k"]},
            {"model": "MV13", "count": 6, "name_prefix": "HQ-CAM-MINI", "tags": ["camera", "indoor", "mini-dome"]},
        ],
        "sensors": [
            {"model": "MT14", "count": 10, "name_prefix": "HQ-DOOR", "tags": ["sensor", "door"]},
            {"model": "MT10", "count": 8, "name_prefix": "HQ-TEMP", "tags": ["sensor", "temperature"]},
        ],
    }

    hq_devices, hq_availabilities, hq_statuses = device_gen.generate_devices_for_network(
        network_id=hq_network_id,
        organization_id=org_id,
        location=hq_location,
        config=hq_device_config,
        network_octet=10
    )
    devices.extend(hq_devices)
    device_availabilities.extend(hq_availabilities)
    device_statuses.extend(hq_statuses)

    # HQ VLANs
    hq_vlans = network_gen.generate_vlans_for_network(
        network_id=hq_network_id,
        vlan_types=["corporate", "guest", "voice", "iot", "management", "server"],
        base_third_octet=10
    )
    vlans.extend(hq_vlans)

    # HQ VLAN Profiles
    hq_vlan_profile = network_gen.generate_vlan_profile(
        network_id=hq_network_id,
        profile_id="hq-standard",
        name="HQ Standard",
        vlan_names=["Corporate", "Guest", "Voice"],
        is_default=True
    )
    vlan_profiles.append(hq_vlan_profile)

    # HQ VPN Config (Hub)
    hq_vpn_subnets = [
        network_gen.generate_vpn_subnet(vlan["subnet"], use_vpn=True)
        for vlan in hq_vlans
    ]
    hq_vpn = network_gen.generate_vpn_config(
        network_id=hq_network_id,
        mode="hub",
        subnets=hq_vpn_subnets
    )
    vpn_configs.append({"network_id": hq_network_id, "config": hq_vpn})

    # HQ Clients - 200 clients (with Smart TVs, Printers for conference rooms)
    hq_net_clients, hq_dev_clients = client_gen.generate_clients_for_network(
        network_id=hq_network_id,
        vlans=hq_vlans,
        count=200,
        devices=hq_devices,
        required_manufacturers=["Samsung TV", "Samsung TV", "Samsung TV", "LG TV", "LG TV",
                                "HP Printer", "HP Printer", "HP Printer", "Canon", "Epson"]
    )
    network_clients.extend(hq_net_clients)
    device_clients.update(hq_dev_clients)

    # ====================================
    # Branch Networks (Spokes)
    # ====================================
    branch_configs = [
        # Large branches (50+ clients) - with cameras, Smart TVs for conference rooms, HP Printers
        {"name": "Branch-NYC", "model": "MX85", "switches": [{"model": "MS250-48", "count": 2}], "aps": [{"model": "MR56", "count": 8}], "cameras": [{"model": "MV33", "count": 4}, {"model": "MV63", "count": 2}], "clients": 60,
         "required_clients": ["Samsung TV", "Samsung TV", "LG TV", "HP Printer", "HP Printer", "Canon"]},
        {"name": "Branch-Chicago", "model": "MX85", "switches": [{"model": "MS250-48", "count": 2}], "aps": [{"model": "MR56", "count": 6}], "cameras": [{"model": "MV23", "count": 3}, {"model": "MV63X", "count": 2}], "clients": 55,
         "required_clients": ["Samsung TV", "LG TV", "HP Printer", "HP Printer", "Epson"]},
        {"name": "Branch-LA", "model": "MX75", "switches": [{"model": "MS225-48", "count": 2}], "aps": [{"model": "MR46", "count": 6}], "cameras": [{"model": "MV13", "count": 4}], "clients": 50,
         "required_clients": ["Samsung TV", "LG TV", "HP Printer", "Canon"]},
        {"name": "Branch-Seattle", "model": "MX75", "switches": [{"model": "MS225-48", "count": 2}], "aps": [{"model": "MR46", "count": 5}], "cameras": [{"model": "MV23X", "count": 3}], "clients": 45,
         "required_clients": ["Samsung TV", "HP Printer", "Epson"]},
        {"name": "Branch-Austin", "model": "MX75", "switches": [{"model": "MS225-48", "count": 1}], "aps": [{"model": "MR46", "count": 5}], "cameras": [{"model": "MV13M", "count": 2}], "clients": 40,
         "required_clients": ["LG TV", "HP Printer"]},

        # Medium branches (30 clients each) - some with cameras
        {"name": "Branch-Denver", "model": "MX68", "switches": [{"model": "MS225-48", "count": 1}], "aps": [{"model": "MR46", "count": 4}], "cameras": [{"model": "MV13", "count": 2}], "clients": 35,
         "required_clients": ["HP Printer", "Canon"]},
        # Boston - Medical/Healthcare branch with medical devices
        {"name": "Branch-Boston-Medical", "model": "MX68", "switches": [{"model": "MS225-48", "count": 1}], "aps": [{"model": "MR46", "count": 4}], "cameras": [{"model": "MV33M", "count": 2}], "clients": 40,
         "required_clients": ["GE Healthcare", "GE Healthcare", "Philips Medical", "Philips Medical", "HP Printer", "Epson"]},
        {"name": "Branch-Atlanta", "model": "MX68", "switches": [{"model": "MS120-24", "count": 1}], "aps": [{"model": "MR36", "count": 3}], "clients": 30,
         "required_clients": ["HP Printer"]},
        {"name": "Branch-Miami", "model": "MX68", "switches": [{"model": "MS120-24", "count": 1}], "aps": [{"model": "MR36", "count": 3}], "clients": 30,
         "required_clients": ["HP Printer", "Samsung TV"]},
        {"name": "Branch-Dallas", "model": "MX68W", "switches": [{"model": "MS120-24", "count": 1}], "aps": [{"model": "MR36", "count": 3}], "sensors": [{"model": "MT10", "count": 2}], "clients": 30,
         "required_clients": ["HP Printer"]},

        # Small branches (15-20 clients each)
        {"name": "Branch-Phoenix", "model": "MX68W", "switches": [], "aps": [{"model": "MR33", "count": 2}], "clients": 20},
        {"name": "Branch-Portland", "model": "MX68W", "switches": [], "aps": [{"model": "MR33", "count": 2}], "clients": 20},
        {"name": "Branch-Minneapolis", "model": "MX67", "switches": [], "aps": [{"model": "MR33", "count": 2}], "clients": 18},
        {"name": "Branch-Detroit", "model": "MX67", "switches": [], "aps": [{"model": "MR33", "count": 2}], "clients": 18},
        {"name": "Branch-Philly", "model": "MX67", "switches": [], "aps": [{"model": "MR33", "count": 2}], "clients": 18},

        # Remote/Cellular sites - warehouse has cameras
        {"name": "Remote-SanDiego", "model": "MX67C", "cellular": [{"model": "MG41"}], "switches": [], "aps": [{"model": "MR30H", "count": 1}], "clients": 10},
        {"name": "Remote-Houston", "model": "MX67C", "cellular": [{"model": "MG41"}], "switches": [], "aps": [{"model": "MR30H", "count": 1}], "clients": 10},
        {"name": "Remote-Charlotte", "model": "MX67C", "cellular": [{"model": "MG41"}], "switches": [], "aps": [{"model": "MR30H", "count": 1}], "clients": 8},
        {"name": "Remote-SaltLake", "model": "MX67C", "cellular": [{"model": "MG41"}], "switches": [], "aps": [], "clients": 5},
        {"name": "Remote-Warehouse", "model": "MX67C", "cellular": [{"model": "MG21"}], "switches": [], "aps": [], "cameras": [{"model": "MV72", "count": 6}, {"model": "MV63", "count": 4}], "sensors": [{"model": "MT14", "count": 8}, {"model": "MT12", "count": 4}], "clients": 3},
    ]

    for i, branch_config in enumerate(branch_configs):
        location = US_LOCATIONS[(i + 1) % len(US_LOCATIONS)]
        network_id = f"N_BR{i + 1:03d}"

        # Create network
        branch_network = network_gen.generate_network(
            network_id=network_id,
            organization_id=org_id,
            name=branch_config["name"],
            product_types=_get_product_types(branch_config),
            timezone=location["tz"],
            tags=["spoke", "branch"],
            notes=f"Branch office in {location['city']}, {location['state']}"
        )
        networks.append(branch_network)

        # Create device config with proper infrastructure tags
        dev_config = {
            "appliances": [{"model": branch_config["model"], "name": f"{branch_config['name']}-MX", "tags": ["spoke", "security-appliance"]}],
            "switches": branch_config.get("switches", []),
            "wireless": branch_config.get("aps", []),
            "cellular": branch_config.get("cellular", []),
            "cameras": branch_config.get("cameras", []),
            "sensors": branch_config.get("sensors", []),
        }

        # Add name prefixes and infrastructure tags
        for sw in dev_config["switches"]:
            sw["name_prefix"] = f"{branch_config['name']}-SW"
            sw["tags"] = ["switch", "network-infrastructure"]
        for ap in dev_config["wireless"]:
            ap["name_prefix"] = f"{branch_config['name']}-AP"
            ap["tags"] = ["wireless-ap", "network-infrastructure"]
        for mg in dev_config["cellular"]:
            mg["name"] = f"{branch_config['name']}-MG"
            mg["tags"] = ["cellular-gateway", "wan-backup"]
        for cam in dev_config["cameras"]:
            cam["name_prefix"] = f"{branch_config['name']}-CAM"
            cam["tags"] = ["camera", "security"]
        for sensor in dev_config["sensors"]:
            sensor["name_prefix"] = f"{branch_config['name']}-SENSOR"
            sensor["tags"] = ["sensor", "iot"]

        # Generate devices
        branch_devices, branch_availabilities, branch_statuses = device_gen.generate_devices_for_network(
            network_id=network_id,
            organization_id=org_id,
            location=location,
            config=dev_config,
            network_octet=20 + i
        )
        devices.extend(branch_devices)
        device_availabilities.extend(branch_availabilities)
        device_statuses.extend(branch_statuses)

        # VLANs (simpler for branches)
        branch_vlans = network_gen.generate_vlans_for_network(
            network_id=network_id,
            vlan_types=["corporate", "guest", "voice"] if branch_config["clients"] > 20 else ["corporate", "guest"],
            base_third_octet=20 + i * 5  # Keep in valid range (20-115 for 20 branches)
        )
        vlans.extend(branch_vlans)

        # VPN Config (Spoke)
        branch_vpn_subnets = [
            network_gen.generate_vpn_subnet(vlan["subnet"], use_vpn=True)
            for vlan in branch_vlans
        ]
        branch_vpn = network_gen.generate_vpn_config(
            network_id=network_id,
            mode="spoke",
            subnets=branch_vpn_subnets,
            hubs=[{"hubId": hq_network_id, "useDefaultRoute": True}]
        )
        vpn_configs.append({"network_id": network_id, "config": branch_vpn})

        # Cellular subnet pool for cellular sites
        if branch_config.get("cellular"):
            cellular_pool = network_gen.generate_cellular_subnet_pool(
                network_id=network_id,
                cidr=f"10.{200 + i}.0.0",
                mask=16
            )
            cellular_subnet_pools.append({"network_id": network_id, "config": cellular_pool})

        # Clients (with optional required device types from config)
        branch_net_clients, branch_dev_clients = client_gen.generate_clients_for_network(
            network_id=network_id,
            vlans=branch_vlans,
            count=branch_config["clients"],
            devices=branch_devices,
            required_manufacturers=branch_config.get("required_clients", [])
        )
        network_clients.extend(branch_net_clients)
        device_clients.update(branch_dev_clients)

    # ====================================
    # Return complete topology
    # ====================================
    return {
        "topology_name": "hub_spoke",
        "description": "Enterprise hub-spoke VPN topology with HQ campus and 20 branch offices",
        "organizations": organizations,
        "networks": networks,
        "devices": devices,
        "device_availabilities": device_availabilities,
        "device_statuses": device_statuses,
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


def _get_product_types(config: dict) -> list[str]:
    """Determine product types based on device configuration."""
    types = ["appliance"]
    if config.get("switches"):
        types.append("switch")
    if config.get("aps"):
        types.append("wireless")
    if config.get("cellular"):
        types.append("cellularGateway")
    if config.get("cameras"):
        types.append("camera")
    if config.get("sensors"):
        types.append("sensor")
    return types
