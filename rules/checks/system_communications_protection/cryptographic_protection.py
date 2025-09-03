class CryptographicProtectionCheck:
    def check_aws(self, data):
        """Check AWS cryptographic protection and key management"""
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
                "details": "No AWS data found for cryptographic protection analysis"
            }

        # Analyze cryptographic protection
        crypto_indicators = []
        crypto_issues = []
        
        # Check S3 encryption
        if s3_data:
            total_buckets = 0
            buckets_with_encryption = 0
            buckets_with_kms = 0
            
            for region, region_s3 in s3_data.items():
                buckets = region_s3.get('buckets', {})
                bucket_encryption = region_s3.get('bucket_encryption', {})
                
                for bucket_name in buckets:
                    total_buckets += 1
                    
                    # Check for encryption
                    if bucket_name in bucket_encryption and bucket_encryption[bucket_name]:
                        buckets_with_encryption += 1
                        
                        # Check for KMS encryption
                        encryption_config = bucket_encryption[bucket_name]
                        if encryption_config.get('ServerSideEncryptionConfiguration'):
                            rules = encryption_config['ServerSideEncryptionConfiguration'].get('Rules', [])
                            for rule in rules:
                                if rule.get('ApplyServerSideEncryptionByDefault'):
                                    sse_config = rule['ApplyServerSideEncryptionByDefault']
                                    if sse_config.get('SSEAlgorithm') == 'aws:kms':
                                        buckets_with_kms += 1
                                        break
            
            if total_buckets > 0:
                crypto_indicators.append(f"{total_buckets} S3 buckets")
                
                if buckets_with_encryption > 0:
                    crypto_indicators.append(f"{buckets_with_encryption} buckets with encryption")
                else:
                    crypto_issues.append("No S3 buckets with encryption")
                
                if buckets_with_kms > 0:
                    crypto_indicators.append(f"{buckets_with_kms} buckets with KMS encryption")
                else:
                    crypto_issues.append("No S3 buckets with KMS encryption")
            else:
                crypto_indicators.append("No S3 buckets found")
        
        # Check EC2 volume encryption
        if ec2_data:
            total_volumes = 0
            encrypted_volumes = 0
            volumes_with_kms = 0
            
            for region, region_ec2 in ec2_data.items():
                volumes = region_ec2.get('volumes', {})
                
                for volume_id, volume_data in volumes.items():
                    total_volumes += 1
                    
                    # Check for encryption
                    if volume_data.get('encrypted', False):
                        encrypted_volumes += 1
                        
                        # Check for KMS encryption
                        kms_key_id = volume_data.get('kms_key_id')
                        if kms_key_id and kms_key_id != 'alias/aws/ebs':
                            volumes_with_kms += 1
            
            if total_volumes > 0:
                crypto_indicators.append(f"{total_volumes} EBS volumes")
                
                if encrypted_volumes > 0:
                    crypto_indicators.append(f"{encrypted_volumes} encrypted volumes")
                else:
                    crypto_issues.append("No encrypted EBS volumes")
                
                if volumes_with_kms > 0:
                    crypto_indicators.append(f"{volumes_with_kms} volumes with custom KMS keys")
                else:
                    crypto_issues.append("No EBS volumes with custom KMS keys")
            else:
                crypto_indicators.append("No EBS volumes found")
        
        # Check CloudTrail encryption
        if cloudtrail_data:
            trails = cloudtrail_data.get('trails', {})
            
            trails_with_encryption = 0
            for trail_name, trail_data in trails.items():
                if trail_data.get('kms_key_id'):
                    trails_with_encryption += 1
            
            if trails:
                crypto_indicators.append(f"{len(trails)} CloudTrail trails")
                
                if trails_with_encryption > 0:
                    crypto_indicators.append(f"{trails_with_encryption} trails with KMS encryption")
                else:
                    crypto_issues.append("No CloudTrail trails with KMS encryption")
            else:
                crypto_indicators.append("No CloudTrail trails found")
        
        # Check for log file validation (cryptographic integrity)
        if cloudtrail_data:
            trails = cloudtrail_data.get('trails', {})
            
            trails_with_validation = 0
            for trail_name, trail_data in trails.items():
                if trail_data.get('log_file_validation_enabled', False):
                    trails_with_validation += 1
            
            if trails_with_validation > 0:
                crypto_indicators.append(f"{trails_with_validation} trails with log file validation")
            else:
                crypto_issues.append("No CloudTrail log file validation")

        # Determine compliance status
        if crypto_issues:
            status = "NON_COMPLIANT"
            details = f"Cryptographic protection issues: {', '.join(crypto_issues)}"
        elif len(crypto_indicators) < 4:
            status = "PARTIAL"
            details = f"Basic cryptographic protection. {', '.join(crypto_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive cryptographic protection. {', '.join(crypto_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace cryptographic protection check not implemented"
        } 