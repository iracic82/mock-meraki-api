"""
Pydantic schemas for Meraki API responses.

These schemas document the expected response formats and can be used
for validation if needed.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OrganizationApi(BaseModel):
    """Organization API settings."""
    enabled: bool = True


class OrganizationLicensing(BaseModel):
    """Organization licensing information."""
    model: str = "co-term"


class OrganizationCloudRegionHost(BaseModel):
    """Cloud region host details."""
    name: str = "United States"


class OrganizationCloudRegion(BaseModel):
    """Cloud region details."""
    name: str = "North America"
    host: OrganizationCloudRegionHost = Field(default_factory=OrganizationCloudRegionHost)


class OrganizationCloud(BaseModel):
    """Organization cloud settings."""
    region: OrganizationCloudRegion = Field(default_factory=OrganizationCloudRegion)


class Organization(BaseModel):
    """Meraki Organization response schema."""
    id: str
    name: str
    url: str
    api: OrganizationApi = Field(default_factory=OrganizationApi)
    licensing: OrganizationLicensing = Field(default_factory=OrganizationLicensing)
    cloud: OrganizationCloud = Field(default_factory=OrganizationCloud)


class Network(BaseModel):
    """Meraki Network response schema."""
    id: str
    organizationId: str
    name: str
    productTypes: list[str]
    timeZone: str
    tags: list[str] = []
    enrollmentString: Optional[str] = None
    url: str
    notes: str = ""
    isBoundToConfigTemplate: bool = False


class Device(BaseModel):
    """Meraki Device response schema."""
    serial: str
    name: str
    mac: str
    networkId: str
    organizationId: str
    model: str
    productType: str
    firmware: str
    lanIp: Optional[str] = None
    wan1Ip: Optional[str] = None
    wan2Ip: Optional[str] = None
    tags: list[str] = []
    lat: float
    lng: float
    address: str = ""
    notes: str = ""
    url: str
    configurationUpdatedAt: str


class DeviceAvailability(BaseModel):
    """Meraki Device Availability response schema."""
    serial: str
    name: str
    mac: str
    networkId: str
    productType: str
    status: str  # online, alerting, offline, dormant
    lastReportedAt: str


class VLAN(BaseModel):
    """Meraki VLAN response schema."""
    id: str
    networkId: str
    name: str
    applianceIp: str
    subnet: str
    fixedIpAssignments: dict = {}
    reservedIpRanges: list = []
    dnsNameservers: str = "upstream_dns"
    dhcpHandling: str = "Run a DHCP server"
    dhcpLeaseTime: str = "1 day"
    dhcpBootOptionsEnabled: bool = False
    dhcpOptions: list = []
    vpnNatSubnet: Optional[str] = None


class VLANProfile(BaseModel):
    """Meraki VLAN Profile response schema."""
    iname: str
    name: str
    isDefault: bool = False
    vlanNames: list[dict] = []
    vlanGroups: list = []


class ClientUsage(BaseModel):
    """Client bandwidth usage."""
    sent: int = 0
    recv: int = 0


class Client(BaseModel):
    """Meraki Client response schema."""
    id: str
    mac: str
    ip: Optional[str] = None
    ip6: Optional[str] = None
    description: Optional[str] = None
    firstSeen: str
    lastSeen: str
    manufacturer: Optional[str] = None
    os: Optional[str] = None
    user: Optional[str] = None
    vlan: Optional[str] = None
    ssid: Optional[str] = None
    switchport: Optional[str] = None
    status: str = "Online"
    notes: str = ""
    smInstalled: bool = False
    recentDeviceSerial: Optional[str] = None
    recentDeviceName: Optional[str] = None
    recentDeviceConnection: Optional[str] = None
    usage: ClientUsage = Field(default_factory=ClientUsage)


class VPNSubnet(BaseModel):
    """VPN subnet configuration."""
    localSubnet: str
    useVpn: bool = True
    nat: dict = {"enabled": False}


class VPNHub(BaseModel):
    """VPN hub reference."""
    hubId: str
    useDefaultRoute: bool = False


class SiteToSiteVPN(BaseModel):
    """Site-to-site VPN configuration."""
    mode: str  # none, hub, spoke
    hubs: list[VPNHub] = []
    subnets: list[VPNSubnet] = []


class CellularSubnetPoolSubnet(BaseModel):
    """Cellular subnet pool subnet."""
    serial: Optional[str] = None
    name: str
    applianceIp: str
    subnet: str


class CellularSubnetPool(BaseModel):
    """Cellular gateway subnet pool configuration."""
    deploymentMode: str = "passthrough"
    cidr: str = ""
    mask: int = 0
    subnets: list[CellularSubnetPoolSubnet] = []
