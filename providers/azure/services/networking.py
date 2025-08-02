from providers.service import BaseService, service_class
import random
import ipaddress


@service_class
class NetworkingService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        # No real clients needed for mock data

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

        # Generate mock Virtual Networks
        print("Generating mock Virtual Networks...")
        vnet_count = random.randint(2, 5)
        for i in range(vnet_count):
            vnet_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Network/virtualNetworks/mock-vnet-{i}"
            vnet_dict = self._generate_mock_vnet(i)
            data["virtual_networks"][vnet_id] = vnet_dict
            print(f"Generated Virtual Network: mock-vnet-{i}")

            # Generate subnets for this VNet
            subnet_count = random.randint(2, 6)
            for j in range(subnet_count):
                subnet_id = f"{vnet_id}/subnets/subnet-{j}"
                subnet_dict = self._generate_mock_subnet(j, vnet_id, i)
                data["subnets"][subnet_id] = subnet_dict

        # Generate mock Network Security Groups
        print("Generating mock Network Security Groups...")
        nsg_count = random.randint(3, 8)
        for i in range(nsg_count):
            nsg_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Network/networkSecurityGroups/mock-nsg-{i}"
            nsg_dict = self._generate_mock_nsg(i)
            data["network_security_groups"][nsg_id] = nsg_dict
            print(f"Generated NSG: mock-nsg-{i}")

        # Generate mock Network Interfaces
        print("Generating mock Network Interfaces...")
        nic_count = random.randint(5, 12)
        for i in range(nic_count):
            nic_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Network/networkInterfaces/mock-nic-{i}"
            nic_dict = self._generate_mock_nic(i)
            data["network_interfaces"][nic_id] = nic_dict
            print(f"Generated NIC: mock-nic-{i}")

        # Generate mock Public IP Addresses
        print("Generating mock Public IP Addresses...")
        pip_count = random.randint(3, 8)
        for i in range(pip_count):
            pip_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Network/publicIPAddresses/mock-pip-{i}"
            pip_dict = self._generate_mock_public_ip(i)
            data["public_ip_addresses"][pip_id] = pip_dict
            print(f"Generated Public IP: mock-pip-{i}")

        # Generate mock Load Balancers
        print("Generating mock Load Balancers...")
        lb_count = random.randint(1, 3)
        for i in range(lb_count):
            lb_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i}/providers/Microsoft.Network/loadBalancers/mock-lb-{i}"
            lb_dict = self._generate_mock_load_balancer(i)
            data["load_balancers"][lb_id] = lb_dict
            print(f"Generated Load Balancer: mock-lb-{i}")

        return data

    def _generate_mock_vnet(self, index):
        """Generate mock Virtual Network data"""
        locations = ["eastus", "westus2", "centralus", "northeurope"]
        address_spaces = ["10.0.0.0/16", "172.16.0.0/12", "192.168.0.0/16", "10.1.0.0/16"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/virtualNetworks/mock-vnet-{index}",
            "name": f"mock-vnet-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "address_space": [random.choice(address_spaces)],
            "provisioning_state": "Succeeded",
            "subnets": [f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/virtualNetworks/mock-vnet-{index}/subnets/subnet-{j}" for j in range(random.randint(2, 4))],
            "enable_ddos_protection": random.choice([True, False]),
            "enable_vm_protection": random.choice([True, False]),
            "tags": {
                "Environment": random.choice(["Dev", "Test", "Prod"]),
                "Network": f"VNet{index}",
            },
        }

    def _generate_mock_subnet(self, index, vnet_id, vnet_index):
        """Generate mock Subnet data"""
        # Generate subnet CIDR based on VNet address space
        base_network = f"10.{vnet_index}.{index}.0/24"
        
        return {
            "id": f"{vnet_id}/subnets/subnet-{index}",
            "name": f"subnet-{index}",
            "vnet_id": vnet_id,
            "address_prefix": base_network,
            "provisioning_state": "Succeeded",
            "network_security_group_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{vnet_index%3}/providers/Microsoft.Network/networkSecurityGroups/mock-nsg-{index}" if random.choice([True, False]) else None,
            "route_table_id": None,
        }

    def _generate_mock_nsg(self, index):
        """Generate mock Network Security Group data"""
        locations = ["eastus", "westus2", "centralus"]
        
        # Generate some mock security rules
        security_rules = []
        rule_count = random.randint(2, 8)
        for i in range(rule_count):
            security_rules.append({
                "name": f"AllowRule{i}",
                "protocol": random.choice(["TCP", "UDP", "*"]),
                "source_port_range": "*",
                "destination_port_range": random.choice(["80", "443", "22", "3389", "8080"]),
                "source_address_prefix": random.choice(["*", "10.0.0.0/8", "Internet"]),
                "destination_address_prefix": "*",
                "access": random.choice(["Allow", "Deny"]),
                "priority": 100 + i * 10,
                "direction": random.choice(["Inbound", "Outbound"]),
            })
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/networkSecurityGroups/mock-nsg-{index}",
            "name": f"mock-nsg-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "provisioning_state": "Succeeded",
            "security_rules": security_rules,
            "tags": {
                "Purpose": random.choice(["Web", "Database", "Application"]),
                "Tier": random.choice(["Frontend", "Backend", "DMZ"]),
            },
        }

    def _generate_mock_nic(self, index):
        """Generate mock Network Interface data"""
        locations = ["eastus", "westus2", "centralus"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/networkInterfaces/mock-nic-{index}",
            "name": f"mock-nic-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "provisioning_state": "Succeeded",
            "mac_address": f"00-0D-3A-{random.randint(10,99):02X}-{random.randint(10,99):02X}-{random.randint(10,99):02X}",
            "primary": random.choice([True, False]),
            "enable_accelerated_networking": random.choice([True, False]),
            "enable_ip_forwarding": random.choice([True, False]),
            "ip_configurations": [
                {
                    "name": "ipconfig1",
                    "private_ip_address": f"10.{index%3}.{random.randint(0,255)}.{random.randint(4,254)}",
                    "private_ip_allocation_method": "Dynamic",
                    "subnet_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/virtualNetworks/mock-vnet-{index%3}/subnets/subnet-0",
                    "public_ip_address_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/publicIPAddresses/mock-pip-{index}" if random.choice([True, False]) else None,
                }
            ],
            "tags": {
                "Owner": f"VM-{index}",
                "Environment": random.choice(["Dev", "Test", "Prod"]),
            },
        }

    def _generate_mock_public_ip(self, index):
        """Generate mock Public IP Address data"""
        locations = ["eastus", "westus2", "centralus"]
        allocation_methods = ["Static", "Dynamic"]
        
        # Generate a fake public IP address
        ip_address = f"{random.randint(1,223)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/publicIPAddresses/mock-pip-{index}",
            "name": f"mock-pip-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "ip_address": ip_address,
            "provisioning_state": "Succeeded",
            "public_ip_allocation_method": random.choice(allocation_methods),
            "public_ip_address_version": "IPv4",
            "idle_timeout_in_minutes": random.choice([4, 10, 15, 30]),
            "tags": {
                "Service": random.choice(["Web", "API", "Database"]),
                "Environment": random.choice(["Dev", "Test", "Prod"]),
            },
        }

    def _generate_mock_load_balancer(self, index):
        """Generate mock Load Balancer data"""
        locations = ["eastus", "westus2", "centralus"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Network/loadBalancers/mock-lb-{index}",
            "name": f"mock-lb-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index}",
            "provisioning_state": "Succeeded",
            "frontend_ip_configurations": [
                {
                    "name": "LoadBalancerFrontEnd",
                    "private_ip_address": None,
                    "subnet_id": None,
                    "public_ip_address_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Network/publicIPAddresses/mock-pip-lb-{index}",
                }
            ],
            "backend_address_pools": [f"BackendPool{i}" for i in range(random.randint(1, 3))],
            "load_balancing_rules": [
                {
                    "name": f"HTTPRule{i}",
                    "protocol": "TCP",
                    "frontend_port": 80 + i,
                    "backend_port": 8080 + i,
                }
                for i in range(random.randint(1, 3))
            ],
            "tags": {
                "Application": random.choice(["WebApp", "API", "Database"]),
                "Tier": "LoadBalancer",
            },
        } 