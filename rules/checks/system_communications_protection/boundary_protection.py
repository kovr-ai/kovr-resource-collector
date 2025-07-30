class BoundaryProtectionCheck:
    def check_aws(self, data):
        """Check AWS boundary protection (security groups, NACLs, VPC configuration)"""
        security_group_issues = []
        vpc_issues = []
        public_subnet_issues = []
        
        # Check security groups across all regions
        for region, region_data in data.items():
            if 'ec2' in region_data:
                ec2_data = region_data['ec2']
                
                # Check security groups
                security_groups = ec2_data.get('security_groups', {})
                for sg_id, sg_data in security_groups.items():
                    # Check for overly permissive inbound rules
                    inbound_rules = sg_data.get('inbound_rules', [])
                    for rule in inbound_rules:
                        # Check for 0.0.0.0/0 (any IP) access
                        ip_ranges = rule.get('ip_ranges', [])
                        for ip_range in ip_ranges:
                            if ip_range == '0.0.0.0/0':
                                port_range = rule.get('port_range', {})
                                from_port = port_range.get('from')
                                to_port = port_range.get('to')
                                
                                # Check for common dangerous ports
                                dangerous_ports = [22, 23, 3389, 3306, 5432, 1433, 1521, 6379, 27017]
                                if from_port and to_port:
                                    for port in range(from_port, to_port + 1):
                                        if port in dangerous_ports:
                                            security_group_issues.append(f"Security group {sg_id} allows 0.0.0.0/0 on port {port}")
                                            break
                
                # Check VPC configuration
                vpcs = ec2_data.get('vpcs', {})
                for vpc_id, vpc_data in vpcs.items():
                    # Check if VPC has internet gateway attached
                    internet_gateways = ec2_data.get('internet_gateways', {})
                    vpc_has_igw = False
                    
                    for igw_id, igw_data in internet_gateways.items():
                        attachments = igw_data.get('attachments', [])
                        for attachment in attachments:
                            if attachment.get('vpc_id') == vpc_id:
                                vpc_has_igw = True
                                break
                    
                    if vpc_has_igw:
                        # Check for public subnets
                        subnets = ec2_data.get('subnets', {})
                        for subnet_id, subnet_data in subnets.items():
                            if subnet_data.get('vpc_id') == vpc_id:
                                if subnet_data.get('map_public_ip_on_launch', False):
                                    public_subnet_issues.append(f"Subnet {subnet_id} in VPC {vpc_id} maps public IPs")
                
                # Check for instances in public subnets
                instances = ec2_data.get('instances', {})
                for instance_id, instance_data in instances.items():
                    subnet_id = instance_data.get('subnet_id')
                    if subnet_id:
                        subnet_data = subnets.get(subnet_id, {})
                        if subnet_data.get('map_public_ip_on_launch', False):
                            public_subnet_issues.append(f"Instance {instance_id} in public subnet {subnet_id}")

        # Determine compliance status
        all_issues = security_group_issues + vpc_issues + public_subnet_issues
        
        if all_issues:
            status = "NON_COMPLIANT"
            details = f"Boundary protection issues found: {', '.join(all_issues[:3])}"  # Show first 3 issues
            if len(all_issues) > 3:
                details += f" and {len(all_issues) - 3} more"
        else:
            status = "COMPLIANT"
            details = "Boundary protection is properly configured"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace check not implemented"
        } 