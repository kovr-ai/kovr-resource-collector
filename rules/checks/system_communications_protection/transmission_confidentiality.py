class TransmissionConfidentialityCheck:
    def check_aws(self, data):
        """Check AWS transmission confidentiality and secure communication"""
        s3_data = {}
        ec2_data = {}
        cloudtrail_data = None
        
        # Collect data from all regions
        for region, region_data in data.items():
            if 's3' in region_data:
                s3_data[region] = region_data['s3']
            if 'ec2' in region_data:
                ec2_data[region] = region_data['ec2']
            if 'cloudtrail' in region_data and not cloudtrail_data:
                cloudtrail_data = region_data['cloudtrail']

        if not s3_data and not ec2_data and not cloudtrail_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No AWS data found for transmission confidentiality analysis"
            }

        # Analyze transmission confidentiality
        transmission_indicators = []
        transmission_issues = []
        
        # Check S3 for secure transmission
        if s3_data:
            total_buckets = 0
            buckets_with_encryption = 0
            buckets_with_ssl = 0
            
            for region, region_s3 in s3_data.items():
                buckets = region_s3.get('buckets', {})
                bucket_encryption = region_s3.get('bucket_encryption', {})
                bucket_policies = region_s3.get('bucket_policies', {})
                
                for bucket_name in buckets:
                    total_buckets += 1
                    
                    # Check for encryption (indicates secure storage)
                    if bucket_name in bucket_encryption and bucket_encryption[bucket_name]:
                        buckets_with_encryption += 1
                    
                    # Check for SSL/TLS requirements in bucket policies
                    if bucket_name in bucket_policies:
                        bucket_policy = bucket_policies[bucket_name]
                        if bucket_policy and 'SecureTransport' in str(bucket_policy):
                            buckets_with_ssl += 1
            
            if total_buckets > 0:
                transmission_indicators.append(f"{total_buckets} S3 buckets")
                
                if buckets_with_encryption > 0:
                    transmission_indicators.append(f"{buckets_with_encryption} buckets with encryption")
                else:
                    transmission_issues.append("No S3 buckets with encryption")
                
                if buckets_with_ssl > 0:
                    transmission_indicators.append(f"{buckets_with_ssl} buckets with SSL requirements")
                else:
                    transmission_issues.append("No S3 buckets with SSL requirements")
            else:
                transmission_indicators.append("No S3 buckets found")
        
        # Check EC2 for secure network communication
        if ec2_data:
            total_instances = 0
            instances_with_security_groups = 0
            instances_with_public_access = 0
            instances_with_private_only = 0
            
            for region, region_ec2 in ec2_data.items():
                instances = region_ec2.get('instances', {})
                security_groups = region_ec2.get('security_groups', {})
                
                for instance_id, instance_data in instances.items():
                    # Handle case where instance_data might be a string
                    if isinstance(instance_data, str):
                        continue
                    
                    # if instance_data.get('state', {}).get('name') in ['running', 'stopped']:
                    #     total_instances += 1
                        
                    #     # Check for security groups (indicates network security)
                    #     instance_security_groups = instance_data.get('security_groups', [])
                    #     if instance_security_groups:
                    #         instances_with_security_groups += 1
                        
                    #     # Check for public access
                    #     if instance_data.get('public_ip_address') or instance_data.get('public_dns_name'):
                    #         instances_with_public_access += 1
                    #     else:
                    #         instances_with_private_only += 1
            
            if total_instances > 0:
                transmission_indicators.append(f"{total_instances} EC2 instances")
                
                if instances_with_security_groups > 0:
                    transmission_indicators.append(f"{instances_with_security_groups} instances with security groups")
                else:
                    transmission_issues.append("No instances with security groups")
                
                if instances_with_public_access > 0:
                    transmission_issues.append(f"{instances_with_public_access} instances with public access")
                
                if instances_with_private_only > 0:
                    transmission_indicators.append(f"{instances_with_private_only} instances with private-only access")
            else:
                transmission_indicators.append("No EC2 instances found")
        
        # Check CloudTrail for secure logging
        if cloudtrail_data:
            trails = cloudtrail_data.get('trails', {})
            
            trails_with_encryption = 0
            trails_with_validation = 0
            
            for trail_name, trail_data in trails.items():
                # Check for KMS encryption
                if trail_data.get('kms_key_id'):
                    trails_with_encryption += 1
                
                # Check for log file validation
                if trail_data.get('log_file_validation_enabled', False):
                    trails_with_validation += 1
            
            if trails:
                transmission_indicators.append(f"{len(trails)} CloudTrail trails")
                
                if trails_with_encryption > 0:
                    transmission_indicators.append(f"{trails_with_encryption} trails with encryption")
                else:
                    transmission_issues.append("No CloudTrail trails with encryption")
                
                if trails_with_validation > 0:
                    transmission_indicators.append(f"{trails_with_validation} trails with log validation")
                else:
                    transmission_issues.append("No CloudTrail log validation")
            else:
                transmission_indicators.append("No CloudTrail trails found")
        
        # Check for VPC configuration (indicates network isolation)
        if ec2_data:
            vpcs_found = False
            for region, region_ec2 in ec2_data.items():
                vpcs = region_ec2.get('vpcs', {})
                if vpcs:
                    vpcs_found = True
                    transmission_indicators.append(f"{len(vpcs)} VPCs in {region}")
                    break
            
            if not vpcs_found:
                transmission_issues.append("No VPCs found")

        # Determine compliance status
        if transmission_issues:
            status = "NON_COMPLIANT"
            details = f"Transmission confidentiality issues: {', '.join(transmission_issues)}"
        elif len(transmission_indicators) < 4:
            status = "PARTIAL"
            details = f"Basic transmission confidentiality. {', '.join(transmission_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive transmission confidentiality. {', '.join(transmission_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace transmission confidentiality check not implemented"
        } 