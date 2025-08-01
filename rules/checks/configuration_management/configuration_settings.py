class ConfigurationSettingsCheck:
    def check_aws(self, data):
        """Check AWS security configuration settings and baseline compliance"""
        iam_data = None
        ec2_data = {}
        s3_data = {}
        
        # Collect data from all regions
        for region, region_data in data.items():
            if 'iam' in region_data and not iam_data:
                iam_data = region_data['iam']
            if 'ec2' in region_data:
                ec2_data[region] = region_data['ec2']
            if 's3' in region_data:
                s3_data[region] = region_data['s3']

        if not iam_data and not ec2_data and not s3_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No AWS data found for configuration analysis"
            }

        # Analyze configuration settings
        config_issues = []
        config_indicators = []
        
        # Check IAM configuration
        if iam_data:
            account_data = iam_data.get('account', {})
            account_summary = account_data.get('summary', {})
            
            # Check for root account MFA
            root_account_mfa = account_summary.get('AccountMFAEnabled', 0)
            if root_account_mfa == 0:
                config_issues.append("Root account MFA not enabled")
            else:
                config_indicators.append("Root account MFA enabled")
            
            # Check for access keys on root account
            root_access_keys = account_summary.get('AccountAccessKeysPresent', 0)
            if root_access_keys > 0:
                config_issues.append("Root account has access keys")
            else:
                config_indicators.append("Root account has no access keys")
            
            # Check for IAM users
            iam_users = account_summary.get('Users', 0)
            if iam_users == 0:
                config_issues.append("No IAM users configured")
            else:
                config_indicators.append(f"{iam_users} IAM users configured")
            
            # Check for IAM groups
            iam_groups = account_summary.get('Groups', 0)
            if iam_groups == 0:
                config_issues.append("No IAM groups configured")
            else:
                config_indicators.append(f"{iam_groups} IAM groups configured")
            
            # Check for IAM roles
            iam_roles = account_summary.get('Roles', 0)
            if iam_roles == 0:
                config_issues.append("No IAM roles configured")
            else:
                config_indicators.append(f"{iam_roles} IAM roles configured")
        
        # Check EC2 configuration across regions
        if ec2_data:
            total_instances = 0
            instances_with_public_ips = 0
            instances_without_encryption = 0
            
            for region, region_ec2 in ec2_data.items():
                instances = region_ec2.get('instances', {})
                volumes = region_ec2.get('volumes', {})
                
                for instance_id, instance_data in instances.items():
                    # Handle case where instance_data might be a string
                    if isinstance(instance_data, str):
                        continue
                    
                    # if instance_data.get('state', {}).get('name') in ['running', 'stopped']:
                    #     total_instances += 1
                        
                    #     # Check for public IPs
                    #     if instance_data.get('public_ip_address'):
                    #         instances_with_public_ips += 1
                        
                    #     # Check attached volumes for encryption
                    #     block_devices = instance_data.get('block_device_mappings', [])
                    #     for device in block_devices:
                    #         volume_id = device.get('ebs', {}).get('volume_id')
                    #         if volume_id and volume_id in volumes:
                    #             if not volumes[volume_id].get('encrypted', False):
                    #                 instances_without_encryption += 1
            
            if total_instances > 0:
                config_indicators.append(f"{total_instances} EC2 instances")
                
                if instances_with_public_ips > 0:
                    config_issues.append(f"{instances_with_public_ips} instances with public IPs")
                
                if instances_without_encryption > 0:
                    config_issues.append(f"{instances_without_encryption} instances without encryption")
            else:
                config_indicators.append("No EC2 instances found")
        
        # Check S3 configuration
        if s3_data:
            total_buckets = 0
            buckets_without_encryption = 0
            buckets_with_public_access = 0
            
            for region, region_s3 in s3_data.items():
                buckets = region_s3.get('buckets', {})
                bucket_encryption = region_s3.get('bucket_encryption', {})
                bucket_public_access = region_s3.get('bucket_public_access_block', {})
                
                for bucket_name in buckets:
                    total_buckets += 1
                    
                    # Check encryption
                    if bucket_name not in bucket_encryption or bucket_encryption[bucket_name] is None:
                        buckets_without_encryption += 1
                    
                    # Check public access
                    if bucket_name in bucket_public_access:
                        public_access = bucket_public_access[bucket_name]
                        if not public_access.get('BlockPublicAcls', True) or not public_access.get('BlockPublicPolicy', True):
                            buckets_with_public_access += 1
            
            if total_buckets > 0:
                config_indicators.append(f"{total_buckets} S3 buckets")
                
                if buckets_without_encryption > 0:
                    config_issues.append(f"{buckets_without_encryption} buckets without encryption")
                
                if buckets_with_public_access > 0:
                    config_issues.append(f"{buckets_with_public_access} buckets with public access")
            else:
                config_indicators.append("No S3 buckets found")

        # Determine compliance status
        if config_issues:
            status = "NON_COMPLIANT"
            details = f"Configuration issues: {', '.join(config_issues)}"
        elif len(config_indicators) < 3:
            status = "PARTIAL"
            details = f"Basic configuration settings. {', '.join(config_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive configuration settings. {', '.join(config_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace configuration settings check not implemented"
        } 