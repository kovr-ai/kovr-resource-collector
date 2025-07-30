from providers.service import BaseService, service_class
import boto3

@service_class
class EC2Service(BaseService):
    def __init__(self, client: boto3.Session):
        super().__init__(client)

    def process(self):
        data = {
            "account": {
                "limits": {},
                "reserved_instances": [],
                "spot_instances": []
            },
            "instances": {},
            "security_groups": {},
            "vpcs": {},
            "subnets": {},
            "route_tables": {},
            "internet_gateways": {},
            "nat_gateways": {},
            "elastic_ips": {},
            "key_pairs": {},
            "volumes": {},
            "snapshots": {},
            "network_interfaces": {},
            "relationships": {
                "instance_security_groups": {},
                "instance_volumes": {},
                "subnet_instances": {},
                "vpc_subnets": {},
                "vpc_security_groups": {},
                "vpc_route_tables": {},
                "vpc_internet_gateways": {},
                "vpc_nat_gateways": {}
            }
        }
        
        client = self.client.client("ec2")
        
        # Get account limits
        try:
            limits_response = client.describe_account_attributes()
            data["account"]["limits"] = {
                attr["AttributeName"]: attr["AttributeValues"][0]["AttributeValue"] 
                for attr in limits_response["AccountAttributes"]
            }
        except Exception as e:
            data["account"]["limits"] = {}
        
        # Get reserved instances
        try:
            reserved_response = client.describe_reserved_instances()
            data["account"]["reserved_instances"] = [
                {
                    "reserved_instances_id": ri["ReservedInstancesId"],
                    "instance_type": ri["InstanceType"],
                    "instance_count": ri["InstanceCount"],
                    "offering_type": ri["OfferingType"],
                    "state": ri["State"],
                    "start": ri["Start"].isoformat(),
                    "end": ri["End"].isoformat(),
                    "fixed_price": ri["FixedPrice"],
                    "usage_price": ri["UsagePrice"],
                    "product_description": ri["ProductDescription"],
                    "availability_zone": ri.get("AvailabilityZone"),
                    "scope": ri["Scope"]
                }
                for ri in reserved_response["ReservedInstances"]
            ]
        except Exception as e:
            data["account"]["reserved_instances"] = []
        
        # Get spot instances
        try:
            spot_response = client.describe_spot_instances()
            data["account"]["spot_instances"] = [
                {
                    "spot_instance_request_id": si["SpotInstanceRequestId"],
                    "instance_id": si.get("InstanceId"),
                    "state": si["State"],
                    "fault": si.get("Fault"),
                    "status": si["Status"],
                    "valid_from": si["ValidFrom"].isoformat(),
                    "valid_until": si["ValidUntil"].isoformat(),
                    "launch_specification": {
                        "image_id": si["LaunchSpecification"]["ImageId"],
                        "instance_type": si["LaunchSpecification"]["InstanceType"],
                        "key_name": si["LaunchSpecification"].get("KeyName"),
                        "security_groups": [
                            sg["GroupName"] for sg in si["LaunchSpecification"]["SecurityGroups"]
                        ]
                    }
                }
                for si in spot_response["SpotInstanceRequests"]
            ]
        except Exception as e:
            data["account"]["spot_instances"] = []
        
        # Get all instances
        try:
            instances_response = client.describe_instances()
            for reservation in instances_response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    data["instances"][instance_id] = {
                        "instance_type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "launch_time": instance["LaunchTime"].isoformat(),
                        "image_id": instance["ImageId"],
                        "vpc_id": instance.get("VpcId"),
                        "subnet_id": instance.get("SubnetId"),
                        "availability_zone": instance["Placement"]["AvailabilityZone"],
                        "key_name": instance.get("KeyName"),
                        "platform": instance.get("Platform"),
                        "monitoring": instance["Monitoring"]["State"],
                        "iam_instance_profile": instance.get("IamInstanceProfile"),
                        "ebs_optimized": instance["EbsOptimized"],
                        "instance_lifecycle": instance.get("InstanceLifecycle"),
                        "security_groups": [
                            sg["GroupId"] for sg in instance["SecurityGroups"]
                        ],
                        "network_interfaces": [
                            ni["NetworkInterfaceId"] for ni in instance["NetworkInterfaces"]
                        ],
                        "block_device_mappings": [
                            {
                                "device_name": bdm["DeviceName"],
                                "ebs": {
                                    "volume_id": bdm["Ebs"]["VolumeId"],
                                    "status": bdm["Ebs"]["Status"],
                                    "attach_time": bdm["Ebs"]["AttachTime"].isoformat(),
                                    "delete_on_termination": bdm["Ebs"]["DeleteOnTermination"]
                                } if "Ebs" in bdm else None
                            }
                            for bdm in instance["BlockDeviceMappings"]
                        ],
                        "tags": {
                            tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])
                        }
                    }
        except Exception as e:
            data["instances"] = {}
        
        # Get all security groups
        try:
            sg_response = client.describe_security_groups()
            for sg in sg_response["SecurityGroups"]:
                sg_id = sg["GroupId"]
                data["security_groups"][sg_id] = {
                    "group_name": sg["GroupName"],
                    "description": sg["Description"],
                    "vpc_id": sg["VpcId"],
                    "inbound_rules": [
                        {
                            "protocol": rule["IpProtocol"],
                            "port_range": {
                                "from": rule.get("FromPort"),
                                "to": rule.get("ToPort")
                            },
                            "ip_ranges": [
                                ip_range["CidrIp"] for ip_range in rule["IpRanges"]
                            ],
                            "user_id_group_pairs": [
                                {
                                    "group_id": pair.get("GroupId"),
                                    "group_name": pair.get("GroupName"),
                                    "user_id": pair.get("UserId"),
                                    "vpc_id": pair.get("VpcId"),
                                    "vpc_peering_connection_id": pair.get("VpcPeeringConnectionId")
                                }
                                for pair in rule["UserIdGroupPairs"]
                            ]
                        }
                        for rule in sg["IpPermissions"]
                    ],
                    "outbound_rules": [
                        {
                            "protocol": rule["IpProtocol"],
                            "port_range": {
                                "from": rule.get("FromPort"),
                                "to": rule.get("ToPort")
                            },
                            "ip_ranges": [
                                ip_range["CidrIp"] for ip_range in rule["IpRanges"]
                            ],
                            "user_id_group_pairs": [
                                {
                                    "group_id": pair.get("GroupId"),
                                    "group_name": pair.get("GroupName"),
                                    "user_id": pair.get("UserId"),
                                    "vpc_id": pair.get("VpcId"),
                                    "vpc_peering_connection_id": pair.get("VpcPeeringConnectionId")
                                }
                                for pair in rule["UserIdGroupPairs"]
                            ]
                        }
                        for rule in sg["IpPermissionsEgress"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in sg.get("Tags", [])
                    }
                }
        except Exception as e:
            data["security_groups"] = {}
        
        # Get all VPCs
        try:
            vpcs_response = client.describe_vpcs()
            for vpc in vpcs_response["Vpcs"]:
                vpc_id = vpc["VpcId"]
                data["vpcs"][vpc_id] = {
                    "cidr_block": vpc["CidrBlock"],
                    "state": vpc["State"],
                    "dhcp_options_id": vpc["DhcpOptionsId"],
                    "instance_tenancy": vpc["InstanceTenancy"],
                    "is_default": vpc["IsDefault"],
                    "cidr_block_association_set": [
                        {
                            "association_id": assoc["AssociationId"],
                            "cidr_block": assoc["CidrBlock"],
                            "state": assoc["CidrBlockState"]["State"]
                        }
                        for assoc in vpc["CidrBlockAssociationSet"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in vpc.get("Tags", [])
                    }
                }
        except Exception as e:
            data["vpcs"] = {}
        
        # Get all subnets
        try:
            subnets_response = client.describe_subnets()
            for subnet in subnets_response["Subnets"]:
                subnet_id = subnet["SubnetId"]
                data["subnets"][subnet_id] = {
                    "vpc_id": subnet["VpcId"],
                    "availability_zone": subnet["AvailabilityZone"],
                    "availability_zone_id": subnet["AvailabilityZoneId"],
                    "cidr_block": subnet["CidrBlock"],
                    "state": subnet["State"],
                    "available_ip_address_count": subnet["AvailableIpAddressCount"],
                    "map_public_ip_on_launch": subnet["MapPublicIpOnLaunch"],
                    "assign_ipv6_address_on_creation": subnet["AssignIpv6AddressOnCreation"],
                    "ipv6_cidr_block_association_set": [
                        {
                            "association_id": assoc["AssociationId"],
                            "ipv6_cidr_block": assoc["Ipv6CidrBlock"],
                            "state": assoc["Ipv6CidrBlockState"]["State"]
                        }
                        for assoc in subnet["Ipv6CidrBlockAssociationSet"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in subnet.get("Tags", [])
                    }
                }
        except Exception as e:
            data["subnets"] = {}
        
        # Get all route tables
        try:
            route_tables_response = client.describe_route_tables()
            for rt in route_tables_response["RouteTables"]:
                rt_id = rt["RouteTableId"]
                data["route_tables"][rt_id] = {
                    "vpc_id": rt["VpcId"],
                    "routes": [
                        {
                            "destination": route["DestinationCidrBlock"],
                            "gateway_id": route.get("GatewayId"),
                            "instance_id": route.get("InstanceId"),
                            "nat_gateway_id": route.get("NatGatewayId"),
                            "network_interface_id": route.get("NetworkInterfaceId"),
                            "vpc_peering_connection_id": route.get("VpcPeeringConnectionId"),
                            "state": route["State"]
                        }
                        for route in rt["Routes"]
                    ],
                    "associations": [
                        {
                            "association_id": assoc["RouteTableAssociationId"],
                            "subnet_id": assoc.get("SubnetId"),
                            "main": assoc["Main"]
                        }
                        for assoc in rt["Associations"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in rt.get("Tags", [])
                    }
                }
        except Exception as e:
            data["route_tables"] = {}
        
        # Get all internet gateways
        try:
            igw_response = client.describe_internet_gateways()
            for igw in igw_response["InternetGateways"]:
                igw_id = igw["InternetGatewayId"]
                data["internet_gateways"][igw_id] = {
                    "state": igw["State"],
                    "attachments": [
                        {
                            "vpc_id": attachment["VpcId"],
                            "state": attachment["State"]
                        }
                        for attachment in igw["Attachments"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in igw.get("Tags", [])
                    }
                }
        except Exception as e:
            data["internet_gateways"] = {}
        
        # Get all NAT gateways
        try:
            nat_response = client.describe_nat_gateways()
            for nat in nat_response["NatGateways"]:
                nat_id = nat["NatGatewayId"]
                data["nat_gateways"][nat_id] = {
                    "state": nat["State"],
                    "subnet_id": nat["SubnetId"],
                    "vpc_id": nat["VpcId"],
                    "create_time": nat["CreateTime"].isoformat(),
                    "delete_time": nat.get("DeleteTime").isoformat() if nat.get("DeleteTime") else None,
                    "nat_gateway_addresses": [
                        {
                            "allocation_id": addr.get("AllocationId"),
                            "network_interface_id": addr.get("NetworkInterfaceId"),
                            "private_ip": addr.get("PrivateIp"),
                            "public_ip": addr.get("PublicIp")
                        }
                        for addr in nat["NatGatewayAddresses"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in nat.get("Tags", [])
                    }
                }
        except Exception as e:
            data["nat_gateways"] = {}
        
        # Get all Elastic IPs
        try:
            eip_response = client.describe_addresses()
            for eip in eip_response["Addresses"]:
                eip_id = eip["AllocationId"]
                data["elastic_ips"][eip_id] = {
                    "public_ip": eip["PublicIp"],
                    "domain": eip["Domain"],
                    "instance_id": eip.get("InstanceId"),
                    "network_interface_id": eip.get("NetworkInterfaceId"),
                    "private_ip_address": eip.get("PrivateIpAddress"),
                    "association_id": eip.get("AssociationId"),
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in eip.get("Tags", [])
                    }
                }
        except Exception as e:
            data["elastic_ips"] = {}
        
        # Get all key pairs
        try:
            keys_response = client.describe_key_pairs()
            for key in keys_response["KeyPairs"]:
                key_name = key["KeyName"]
                data["key_pairs"][key_name] = {
                    "key_fingerprint": key["KeyFingerprint"],
                    "key_type": key["KeyType"],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in key.get("Tags", [])
                    }
                }
        except Exception as e:
            data["key_pairs"] = {}
        
        # Get all volumes
        try:
            volumes_response = client.describe_volumes()
            for volume in volumes_response["Volumes"]:
                volume_id = volume["VolumeId"]
                data["volumes"][volume_id] = {
                    "size": volume["Size"],
                    "volume_type": volume["VolumeType"],
                    "state": volume["State"],
                    "availability_zone": volume["AvailabilityZone"],
                    "create_time": volume["CreateTime"].isoformat(),
                    "encrypted": volume["Encrypted"],
                    "kms_key_id": volume.get("KmsKeyId"),
                    "iops": volume.get("Iops"),
                    "throughput": volume.get("Throughput"),
                    "attachments": [
                        {
                            "instance_id": attachment["InstanceId"],
                            "device": attachment["Device"],
                            "state": attachment["State"],
                            "attach_time": attachment["AttachTime"].isoformat(),
                            "delete_on_termination": attachment["DeleteOnTermation"]
                        }
                        for attachment in volume["Attachments"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in volume.get("Tags", [])
                    }
                }
        except Exception as e:
            data["volumes"] = {}
        
        # Get all snapshots
        try:
            snapshots_response = client.describe_snapshots(OwnerIds=['self'])
            for snapshot in snapshots_response["Snapshots"]:
                snapshot_id = snapshot["SnapshotId"]
                data["snapshots"][snapshot_id] = {
                    "volume_id": snapshot["VolumeId"],
                    "volume_size": snapshot["VolumeSize"],
                    "state": snapshot["State"],
                    "start_time": snapshot["StartTime"].isoformat(),
                    "progress": snapshot["Progress"],
                    "encrypted": snapshot["Encrypted"],
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "description": snapshot.get("Description"),
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in snapshot.get("Tags", [])
                    }
                }
        except Exception as e:
            data["snapshots"] = {}
        
        # Get all network interfaces
        try:
            eni_response = client.describe_network_interfaces()
            for eni in eni_response["NetworkInterfaces"]:
                eni_id = eni["NetworkInterfaceId"]
                data["network_interfaces"][eni_id] = {
                    "subnet_id": eni["SubnetId"],
                    "vpc_id": eni["VpcId"],
                    "availability_zone": eni["AvailabilityZone"],
                    "description": eni.get("Description"),
                    "status": eni["Status"],
                    "mac_address": eni["MacAddress"],
                    "private_ip_address": eni["PrivateIpAddress"],
                    "private_dns_name": eni.get("PrivateDnsName"),
                    "source_dest_check": eni["SourceDestCheck"],
                    "groups": [
                        {
                            "group_name": group["GroupName"],
                            "group_id": group["GroupId"]
                        }
                        for group in eni["Groups"]
                    ],
                    "attachment": {
                        "attachment_id": eni["Attachment"]["AttachmentId"],
                        "instance_id": eni["Attachment"].get("InstanceId"),
                        "instance_owner_id": eni["Attachment"]["InstanceOwnerId"],
                        "device_index": eni["Attachment"]["DeviceIndex"],
                        "status": eni["Attachment"]["Status"],
                        "attach_time": eni["Attachment"]["AttachTime"].isoformat(),
                        "delete_on_termination": eni["Attachment"]["DeleteOnTermation"]
                    } if eni.get("Attachment") else None,
                    "private_ip_addresses": [
                        {
                            "private_ip_address": addr["PrivateIpAddress"],
                            "primary": addr["Primary"],
                            "association": {
                                "public_ip": addr["Association"]["PublicIp"],
                                "public_dns_name": addr["Association"].get("PublicDnsName"),
                                "allocation_id": addr["Association"].get("AllocationId"),
                                "association_id": addr["Association"].get("AssociationId")
                            } if addr.get("Association") else None
                        }
                        for addr in eni["PrivateIpAddresses"]
                    ],
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in eni.get("Tags", [])
                    }
                }
        except Exception as e:
            data["network_interfaces"] = {}
        
        # Build relationships
        self._build_relationships(client, data)
        
        return data
    
    def _build_relationships(self, client, data):
        """Build relationship mappings without duplicating data"""
        
        # Instance-Security Group relationships
        for instance_id, instance in data["instances"].items():
            data["relationships"]["instance_security_groups"][instance_id] = instance["security_groups"]
        
        # Instance-Volume relationships
        for instance_id, instance in data["instances"].items():
            volume_ids = []
            for bdm in instance["block_device_mappings"]:
                if bdm.get("ebs") and bdm["ebs"].get("volume_id"):
                    volume_ids.append(bdm["ebs"]["volume_id"])
            data["relationships"]["instance_volumes"][instance_id] = volume_ids
        
        # Subnet-Instance relationships
        for instance_id, instance in data["instances"].items():
            if instance.get("subnet_id"):
                subnet_id = instance["subnet_id"]
                if subnet_id not in data["relationships"]["subnet_instances"]:
                    data["relationships"]["subnet_instances"][subnet_id] = []
                data["relationships"]["subnet_instances"][subnet_id].append(instance_id)
        
        # VPC-Subnet relationships
        for subnet_id, subnet in data["subnets"].items():
            vpc_id = subnet["vpc_id"]
            if vpc_id not in data["relationships"]["vpc_subnets"]:
                data["relationships"]["vpc_subnets"][vpc_id] = []
            data["relationships"]["vpc_subnets"][vpc_id].append(subnet_id)
        
        # VPC-Security Group relationships
        for sg_id, sg in data["security_groups"].items():
            vpc_id = sg["vpc_id"]
            if vpc_id not in data["relationships"]["vpc_security_groups"]:
                data["relationships"]["vpc_security_groups"][vpc_id] = []
            data["relationships"]["vpc_security_groups"][vpc_id].append(sg_id)
        
        # VPC-Route Table relationships
        for rt_id, rt in data["route_tables"].items():
            vpc_id = rt["vpc_id"]
            if vpc_id not in data["relationships"]["vpc_route_tables"]:
                data["relationships"]["vpc_route_tables"][vpc_id] = []
            data["relationships"]["vpc_route_tables"][vpc_id].append(rt_id)
        
        # VPC-Internet Gateway relationships
        for igw_id, igw in data["internet_gateways"].items():
            for attachment in igw["attachments"]:
                vpc_id = attachment["vpc_id"]
                if vpc_id not in data["relationships"]["vpc_internet_gateways"]:
                    data["relationships"]["vpc_internet_gateways"][vpc_id] = []
                data["relationships"]["vpc_internet_gateways"][vpc_id].append(igw_id)
        
        # VPC-NAT Gateway relationships
        for nat_id, nat in data["nat_gateways"].items():
            vpc_id = nat["vpc_id"]
            if vpc_id not in data["relationships"]["vpc_nat_gateways"]:
                data["relationships"]["vpc_nat_gateways"][vpc_id] = []
            data["relationships"]["vpc_nat_gateways"][vpc_id].append(nat_id)
