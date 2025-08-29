from providers.service import BaseService, service_class
from azure.mgmt.network import NetworkManagementClient


@service_class
class NetworkingService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        self.network_client = NetworkManagementClient(credential, subscription_id)

    def process(self):
        data = {
            "virtual_networks": {},
            "subnets": {},
            "network_security_groups": {},
            "network_interfaces": {},
            "public_ip_addresses": {},
            "load_balancers": {},
            "application_gateways": {},
            "route_tables": {},
        }

        try:
            # Get Virtual Networks
            print("Collecting Virtual Networks...")
            vnets = self.network_client.virtual_networks.list_all()
            for vnet in vnets:
                vnet_dict = self._vnet_to_dict(vnet)
                data["virtual_networks"][vnet.id] = vnet_dict
                print(f"Found Virtual Network: {vnet.name}")

                # Get subnets for this VNet
                if vnet.subnets:
                    for subnet in vnet.subnets:
                        subnet_dict = self._subnet_to_dict(subnet, vnet.id)
                        data["subnets"][subnet.id] = subnet_dict

        except Exception as e:
            print(f"Error collecting Virtual Networks: {str(e)}")
            data["virtual_networks"] = {}

        try:
            # Get Network Security Groups
            print("Collecting Network Security Groups...")
            nsgs = self.network_client.network_security_groups.list_all()
            for nsg in nsgs:
                nsg_dict = self._nsg_to_dict(nsg)
                data["network_security_groups"][nsg.id] = nsg_dict
                print(f"Found NSG: {nsg.name}")

        except Exception as e:
            print(f"Error collecting Network Security Groups: {str(e)}")
            data["network_security_groups"] = {}

        try:
            # Get Network Interfaces
            print("Collecting Network Interfaces...")
            nics = self.network_client.network_interfaces.list_all()
            for nic in nics:
                nic_dict = self._nic_to_dict(nic)
                data["network_interfaces"][nic.id] = nic_dict
                print(f"Found Network Interface: {nic.name}")

        except Exception as e:
            print(f"Error collecting Network Interfaces: {str(e)}")
            data["network_interfaces"] = {}

        try:
            # Get Public IP Addresses
            print("Collecting Public IP Addresses...")
            public_ips = self.network_client.public_ip_addresses.list_all()
            for pip in public_ips:
                pip_dict = self._public_ip_to_dict(pip)
                data["public_ip_addresses"][pip.id] = pip_dict
                print(f"Found Public IP: {pip.name}")

        except Exception as e:
            print(f"Error collecting Public IP Addresses: {str(e)}")
            data["public_ip_addresses"] = {}

        try:
            # Get Load Balancers
            print("Collecting Load Balancers...")
            load_balancers = self.network_client.load_balancers.list_all()
            for lb in load_balancers:
                lb_dict = self._load_balancer_to_dict(lb)
                data["load_balancers"][lb.id] = lb_dict
                print(f"Found Load Balancer: {lb.name}")

        except Exception as e:
            print(f"Error collecting Load Balancers: {str(e)}")
            data["load_balancers"] = {}

        return data

    def _vnet_to_dict(self, vnet):
        """Convert Virtual Network object to dictionary"""
        return {
            "id": vnet.id,
            "name": vnet.name,
            "location": vnet.location,
            "resource_group": vnet.id.split('/')[4] if len(vnet.id.split('/')) > 4 else None,
            "address_space": vnet.address_space.address_prefixes if vnet.address_space else [],
            "provisioning_state": vnet.provisioning_state,
            "subnets": [subnet.id for subnet in (vnet.subnets or [])],
            "tags": dict(vnet.tags) if vnet.tags else {},
        }

    def _subnet_to_dict(self, subnet, vnet_id):
        """Convert Subnet object to dictionary"""
        return {
            "id": subnet.id,
            "name": subnet.name,
            "vnet_id": vnet_id,
            "address_prefix": subnet.address_prefix,
            "provisioning_state": subnet.provisioning_state,
            "network_security_group_id": subnet.network_security_group.id if subnet.network_security_group else None,
            "route_table_id": subnet.route_table.id if subnet.route_table else None,
        }

    def _nsg_to_dict(self, nsg):
        """Convert Network Security Group object to dictionary"""
        return {
            "id": nsg.id,
            "name": nsg.name,
            "location": nsg.location,
            "resource_group": nsg.id.split('/')[4] if len(nsg.id.split('/')) > 4 else None,
            "provisioning_state": nsg.provisioning_state,
            "security_rules": [
                {
                    "name": rule.name,
                    "protocol": rule.protocol,
                    "source_port_range": rule.source_port_range,
                    "destination_port_range": rule.destination_port_range,
                    "source_address_prefix": rule.source_address_prefix,
                    "destination_address_prefix": rule.destination_address_prefix,
                    "access": rule.access,
                    "priority": rule.priority,
                    "direction": rule.direction,
                }
                for rule in (nsg.security_rules or [])
            ],
            "tags": dict(nsg.tags) if nsg.tags else {},
        }

    def _nic_to_dict(self, nic):
        """Convert Network Interface object to dictionary"""
        return {
            "id": nic.id,
            "name": nic.name,
            "location": nic.location,
            "resource_group": nic.id.split('/')[4] if len(nic.id.split('/')) > 4 else None,
            "provisioning_state": nic.provisioning_state,
            "mac_address": nic.mac_address,
            "primary": nic.primary,
            "enable_accelerated_networking": nic.enable_accelerated_networking,
            "enable_ip_forwarding": nic.enable_ip_forwarding,
            "ip_configurations": [
                {
                    "name": config.name,
                    "private_ip_address": config.private_ip_address,
                    "private_ip_allocation_method": config.private_ip_allocation_method,
                    "subnet_id": config.subnet.id if config.subnet else None,
                    "public_ip_address_id": config.public_ip_address.id if config.public_ip_address else None,
                }
                for config in (nic.ip_configurations or [])
            ],
            "tags": dict(nic.tags) if nic.tags else {},
        }

    def _public_ip_to_dict(self, pip):
        """Convert Public IP Address object to dictionary"""
        return {
            "id": pip.id,
            "name": pip.name,
            "location": pip.location,
            "resource_group": pip.id.split('/')[4] if len(pip.id.split('/')) > 4 else None,
            "ip_address": pip.ip_address,
            "provisioning_state": pip.provisioning_state,
            "public_ip_allocation_method": pip.public_ip_allocation_method,
            "public_ip_address_version": pip.public_ip_address_version,
            "idle_timeout_in_minutes": pip.idle_timeout_in_minutes,
            "tags": dict(pip.tags) if pip.tags else {},
        }

    def _load_balancer_to_dict(self, lb):
        """Convert Load Balancer object to dictionary"""
        return {
            "id": lb.id,
            "name": lb.name,
            "location": lb.location,
            "resource_group": lb.id.split('/')[4] if len(lb.id.split('/')) > 4 else None,
            "provisioning_state": lb.provisioning_state,
            "frontend_ip_configurations": [
                {
                    "name": config.name,
                    "private_ip_address": config.private_ip_address,
                    "subnet_id": config.subnet.id if config.subnet else None,
                    "public_ip_address_id": config.public_ip_address.id if config.public_ip_address else None,
                }
                for config in (lb.frontend_ip_configurations or [])
            ],
            "backend_address_pools": [pool.name for pool in (lb.backend_address_pools or [])],
            "load_balancing_rules": [
                {
                    "name": rule.name,
                    "protocol": rule.protocol,
                    "frontend_port": rule.frontend_port,
                    "backend_port": rule.backend_port,
                }
                for rule in (lb.load_balancing_rules or [])
            ],
            "tags": dict(lb.tags) if lb.tags else {},
        } 