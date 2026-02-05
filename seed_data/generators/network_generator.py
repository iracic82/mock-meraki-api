"""
Network and VLAN data generator for Mock Meraki API.

Generates realistic network configurations including:
- Networks with proper product types
- VLAN configurations
- VLAN profiles
- VPN configurations
- Cellular gateway subnet pools
"""

import random
import string
from typing import Optional

# Standard VLAN templates
VLAN_TEMPLATES = {
    "corporate": {
        "id": 10,
        "name": "Corporate",
        "subnet": "192.168.10.0/24",
        "applianceIp": "192.168.10.1",
        "dhcpHandling": "Run a DHCP server",
        "dnsNameservers": "upstream_dns",
    },
    "guest": {
        "id": 20,
        "name": "Guest",
        "subnet": "192.168.20.0/24",
        "applianceIp": "192.168.20.1",
        "dhcpHandling": "Run a DHCP server",
        "dnsNameservers": "upstream_dns",
    },
    "voice": {
        "id": 30,
        "name": "Voice",
        "subnet": "192.168.30.0/24",
        "applianceIp": "192.168.30.1",
        "dhcpHandling": "Run a DHCP server",
        "dnsNameservers": "upstream_dns",
    },
    "iot": {
        "id": 40,
        "name": "IoT",
        "subnet": "192.168.40.0/24",
        "applianceIp": "192.168.40.1",
        "dhcpHandling": "Run a DHCP server",
        "dnsNameservers": "upstream_dns",
    },
    "management": {
        "id": 99,
        "name": "Management",
        "subnet": "192.168.99.0/24",
        "applianceIp": "192.168.99.1",
        "dhcpHandling": "Do not respond to DHCP requests",
        "dnsNameservers": "upstream_dns",
    },
    "server": {
        "id": 50,
        "name": "Servers",
        "subnet": "192.168.50.0/24",
        "applianceIp": "192.168.50.1",
        "dhcpHandling": "Do not respond to DHCP requests",
        "dnsNameservers": "upstream_dns",
    },
}


class NetworkGenerator:
    """Generator for realistic Meraki network data."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)

    def generate_organization(
        self,
        org_id: str,
        name: str,
        region: str = "North America"
    ) -> dict:
        """
        Generate an organization.

        Args:
            org_id: Organization ID
            name: Organization name
            region: Cloud region

        Returns:
            Organization data dictionary
        """
        return {
            "id": org_id,
            "name": name,
            "url": f"https://mock.meraki.com/o/{name.lower().replace(' ', '-')}/manage/organization/overview",
            "api": {
                "enabled": True
            },
            "licensing": {
                "model": "co-term"
            },
            "cloud": {
                "region": {
                    "name": region,
                    "host": {
                        "name": "United States" if region == "North America" else region
                    }
                }
            },
            "management": {
                "details": [
                    {
                        "name": "customer number",
                        "value": f"{random.randint(10000000, 99999999):08d}"
                    }
                ]
            }
        }

    def generate_network(
        self,
        network_id: str,
        organization_id: str,
        name: str,
        product_types: list[str],
        timezone: str,
        tags: Optional[list[str]] = None,
        notes: str = ""
    ) -> dict:
        """
        Generate a network.

        Args:
            network_id: Network ID
            organization_id: Parent organization ID
            name: Network name
            product_types: List of product types (appliance, switch, wireless, etc.)
            timezone: Network timezone
            tags: Optional list of tags
            notes: Optional notes

        Returns:
            Network data dictionary
        """
        return {
            "id": network_id,
            "organizationId": organization_id,
            "name": name,
            "productTypes": product_types,
            "timeZone": timezone,
            "tags": tags or [],
            "enrollmentString": None,
            "url": f"https://mock.meraki.com/{name.replace(' ', '-')}/manage/clients",
            "notes": notes if notes else None,
            "details": None,
            "isBoundToConfigTemplate": False,
            "isVirtual": False
        }

    def generate_vlan(
        self,
        network_id: str,
        vlan_id: int,
        name: str,
        subnet: str,
        appliance_ip: str,
        dhcp_handling: str = "Run a DHCP server",
        dns_nameservers: str = "upstream_dns"
    ) -> dict:
        """
        Generate a VLAN configuration.

        Args:
            network_id: Parent network ID
            vlan_id: VLAN ID
            name: VLAN name
            subnet: VLAN subnet in CIDR notation
            appliance_ip: MX appliance IP on this VLAN
            dhcp_handling: DHCP mode
            dns_nameservers: DNS configuration

        Returns:
            VLAN data dictionary
        """
        # Parse subnet for DHCP pool
        base_ip = subnet.rsplit('.', 1)[0]
        dhcp_start = f"{base_ip}.100"
        dhcp_end = f"{base_ip}.250"

        # Generate interface ID (13-digit numeric string per Meraki API)
        interface_id = ''.join(random.choices(string.digits, k=13))

        return {
            "id": str(vlan_id),
            "interfaceId": interface_id,
            "networkId": network_id,
            "name": name,
            "applianceIp": appliance_ip,
            "subnet": subnet,
            "fixedIpAssignments": {},
            "reservedIpRanges": [],
            "dnsNameservers": dns_nameservers,
            "dhcpHandling": dhcp_handling,
            "dhcpLeaseTime": "1 day",
            "dhcpBootOptionsEnabled": False,
            "dhcpOptions": [],
            "vpnNatSubnet": subnet,
            "mandatoryDhcp": {
                "enabled": False
            },
            "ipv6": {
                "enabled": False
            },
            "dhcpBootFilename": None,
            "dhcpBootNextServer": None,
            "dhcpRelayServerIps": [],
            "groupPolicyId": None,
            "templateVlanType": "same",
            "cidr": subnet,
            "mask": int(subnet.split("/")[1]) if "/" in subnet else 24,
        }

    def generate_vlans_for_network(
        self,
        network_id: str,
        vlan_types: list[str],
        base_third_octet: int = 10
    ) -> list[dict]:
        """
        Generate VLANs for a network based on requested types.

        Args:
            network_id: Network ID
            vlan_types: List of VLAN types (corporate, guest, voice, iot, management)
            base_third_octet: Starting third octet for subnet addressing

        Returns:
            List of VLAN configurations
        """
        vlans = []

        for i, vlan_type in enumerate(vlan_types):
            template = VLAN_TEMPLATES.get(vlan_type, VLAN_TEMPLATES["corporate"])

            # Adjust subnet based on base octet
            vlan_id = template["id"]
            third_octet = base_third_octet + i
            subnet = f"192.168.{third_octet}.0/24"
            appliance_ip = f"192.168.{third_octet}.1"

            vlan = self.generate_vlan(
                network_id=network_id,
                vlan_id=vlan_id,
                name=template["name"],
                subnet=subnet,
                appliance_ip=appliance_ip,
                dhcp_handling=template["dhcpHandling"],
                dns_nameservers=template["dnsNameservers"]
            )
            vlans.append(vlan)

        return vlans

    def generate_vlan_profile(
        self,
        network_id: str,
        profile_id: str,
        name: str,
        vlan_names: list[str],
        is_default: bool = False
    ) -> dict:
        """
        Generate a VLAN profile.

        Args:
            network_id: Network ID
            profile_id: Profile ID
            name: Profile name
            vlan_names: List of VLAN names in this profile
            is_default: Whether this is the default profile

        Returns:
            VLAN profile data dictionary
        """
        return {
            "iname": profile_id,
            "name": name,
            "isDefault": is_default,
            "vlanNames": [{"name": n, "adaptivePolicyGroup": None} for n in vlan_names],
            "vlanGroups": []
        }

    def generate_vpn_config(
        self,
        network_id: str,
        mode: str,
        subnets: list[dict],
        hubs: Optional[list[dict]] = None
    ) -> dict:
        """
        Generate site-to-site VPN configuration.

        Args:
            network_id: Network ID
            mode: VPN mode (none, hub, spoke)
            subnets: List of subnet configurations
            hubs: List of hub configurations (for spoke mode)

        Returns:
            VPN configuration dictionary
        """
        config = {
            "mode": mode,
            "hubs": hubs or [],
            "subnets": subnets
        }

        if mode == "hub":
            config["localStatusPages"] = {
                "enabled": True
            }

        return config

    def generate_vpn_subnet(
        self,
        subnet: str,
        use_vpn: bool = True,
        nat_enabled: bool = False
    ) -> dict:
        """
        Generate a VPN subnet configuration.

        Args:
            subnet: Subnet in CIDR notation
            use_vpn: Whether to include in VPN
            nat_enabled: Whether NAT is enabled

        Returns:
            VPN subnet configuration
        """
        return {
            "localSubnet": subnet,
            "useVpn": use_vpn,
            "nat": {
                "enabled": nat_enabled
            }
        }

    def generate_cellular_subnet_pool(
        self,
        network_id: str,
        cidr: str = "10.200.0.0",
        mask: int = 16
    ) -> dict:
        """
        Generate cellular gateway subnet pool configuration.

        Args:
            network_id: Network ID
            cidr: Base CIDR
            mask: Subnet mask

        Returns:
            Cellular subnet pool configuration
        """
        return {
            "deploymentMode": "routed",
            "cidr": f"{cidr}/{mask}",
            "mask": mask,
            "subnets": [
                {
                    "serial": None,
                    "name": "Subnet 1",
                    "applianceIp": f"{cidr.rsplit('.', 2)[0]}.1.1",
                    "subnet": f"{cidr.rsplit('.', 2)[0]}.1.0/24"
                }
            ]
        }
