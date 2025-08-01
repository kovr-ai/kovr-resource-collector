"""Pydantic models for Azure Networking resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base_models import AzureResource, AzureSku


class VirtualNetworkModel(AzureResource):
    """Azure Virtual Network model."""
    address_space: List[str] = Field(default_factory=list)
    dhcp_options: Dict[str, Any] = Field(default_factory=dict)
    subnets: List[str] = Field(default_factory=list)
    virtual_network_peerings: List[Dict[str, Any]] = Field(default_factory=list)
    enable_ddos_protection: bool = False
    enable_vm_protection: bool = False
    ddos_protection_plan: Optional[Dict[str, Any]] = None
    bgp_communities: Optional[Dict[str, Any]] = None
    flow_timeout_in_minutes: Optional[int] = None


class SubnetModel(BaseModel):
    """Azure Subnet model."""
    id: str
    name: str
    vnet_id: str
    address_prefix: Optional[str] = None
    address_prefixes: List[str] = Field(default_factory=list)
    provisioning_state: Optional[str] = None
    
    # Associated resources
    network_security_group_id: Optional[str] = None
    route_table_id: Optional[str] = None
    nat_gateway_id: Optional[str] = None
    
    # Service endpoints
    service_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    service_endpoint_policies: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Delegation
    delegations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Private endpoint network policies
    private_endpoint_network_policies: Optional[str] = None
    private_link_service_network_policies: Optional[str] = None


class NetworkSecurityGroupModel(AzureResource):
    """Azure Network Security Group model."""
    security_rules: List[Dict[str, Any]] = Field(default_factory=list)
    default_security_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Associated resources
    network_interfaces: List[str] = Field(default_factory=list)
    subnets: List[str] = Field(default_factory=list)
    
    # Flow logs
    flow_logs: List[Dict[str, Any]] = Field(default_factory=list)


class NetworkInterfaceModel(AzureResource):
    """Azure Network Interface model."""
    mac_address: Optional[str] = None
    primary: bool = False
    enable_accelerated_networking: bool = False
    enable_ip_forwarding: bool = False
    
    # IP configurations
    ip_configurations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # DNS settings
    dns_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Associated resources
    network_security_group_id: Optional[str] = None
    virtual_machine_id: Optional[str] = None
    
    # Tap configurations
    tap_configurations: List[Dict[str, Any]] = Field(default_factory=list)


class PublicIPModel(AzureResource):
    """Azure Public IP Address model."""
    ip_address: Optional[str] = None
    public_ip_allocation_method: Optional[str] = None  # Static, Dynamic
    public_ip_address_version: Optional[str] = None  # IPv4, IPv6
    idle_timeout_in_minutes: Optional[int] = None
    
    # DNS settings
    dns_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # IP tags
    ip_tags: List[Dict[str, str]] = Field(default_factory=list)
    
    # Associated resource
    ip_configuration_id: Optional[str] = None
    
    # DDoS settings
    ddos_settings: Optional[Dict[str, Any]] = None
    
    # SKU
    sku: Optional[AzureSku] = None
    
    # Availability zones
    zones: List[str] = Field(default_factory=list)


class LoadBalancerModel(AzureResource):
    """Azure Load Balancer model."""
    sku: Optional[AzureSku] = None
    
    # Frontend IP configurations
    frontend_ip_configurations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Backend address pools
    backend_address_pools: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Load balancing rules
    load_balancing_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Probes
    probes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Inbound NAT rules
    inbound_nat_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Inbound NAT pools
    inbound_nat_pools: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Outbound rules
    outbound_rules: List[Dict[str, Any]] = Field(default_factory=list)


class ApplicationGatewayModel(AzureResource):
    """Azure Application Gateway model."""
    sku: Optional[Dict[str, Any]] = None
    
    # Gateway IP configurations
    gateway_ip_configurations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Frontend IP configurations
    frontend_ip_configurations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Frontend ports
    frontend_ports: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Backend address pools
    backend_address_pools: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Backend HTTP settings
    backend_http_settings_collection: List[Dict[str, Any]] = Field(default_factory=list)
    
    # HTTP listeners
    http_listeners: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Request routing rules
    request_routing_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # SSL certificates
    ssl_certificates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Web application firewall configuration
    web_application_firewall_configuration: Optional[Dict[str, Any]] = None
    
    # Enable HTTP2
    enable_http2: bool = False
    
    # Enable FIPS
    enable_fips: bool = False


class RouteTableModel(AzureResource):
    """Azure Route Table model."""
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    subnets: List[str] = Field(default_factory=list)
    disable_bgp_route_propagation: bool = False


class NetworkingData(BaseModel):
    """Container for all Azure Networking service data."""
    virtual_networks: Dict[str, VirtualNetworkModel] = Field(default_factory=dict)
    subnets: Dict[str, SubnetModel] = Field(default_factory=dict)
    network_security_groups: Dict[str, NetworkSecurityGroupModel] = Field(default_factory=dict)
    network_interfaces: Dict[str, NetworkInterfaceModel] = Field(default_factory=dict)
    public_ip_addresses: Dict[str, PublicIPModel] = Field(default_factory=dict)
    load_balancers: Dict[str, LoadBalancerModel] = Field(default_factory=dict)
    application_gateways: Dict[str, ApplicationGatewayModel] = Field(default_factory=dict)
    route_tables: Dict[str, RouteTableModel] = Field(default_factory=dict)
    
    # Summary statistics
    total_vnets: int = 0
    total_subnets: int = 0
    total_nsgs: int = 0
    total_nics: int = 0
    total_public_ips: int = 0
    total_load_balancers: int = 0
    total_app_gateways: int = 0
    total_route_tables: int = 0
    
    # Security statistics
    nsgs_with_default_rules_only: int = 0
    public_ips_with_ddos_protection: int = 0
    vnets_with_ddos_protection: int = 0
    
    def calculate_statistics(self):
        """Calculate summary statistics from the collected data."""
        self.total_vnets = len(self.virtual_networks)
        self.total_subnets = len(self.subnets)
        self.total_nsgs = len(self.network_security_groups)
        self.total_nics = len(self.network_interfaces)
        self.total_public_ips = len(self.public_ip_addresses)
        self.total_load_balancers = len(self.load_balancers)
        self.total_app_gateways = len(self.application_gateways)
        self.total_route_tables = len(self.route_tables)
        
        # Calculate security statistics
        self.nsgs_with_default_rules_only = sum(
            1 for nsg in self.network_security_groups.values()
            if len(nsg.security_rules) == 0
        )
        
        self.vnets_with_ddos_protection = sum(
            1 for vnet in self.virtual_networks.values()
            if vnet.enable_ddos_protection
        )
        
        self.public_ips_with_ddos_protection = sum(
            1 for pip in self.public_ip_addresses.values()
            if pip.ddos_settings is not None
        ) 