class DataAtRestEncryptionCheck:
    def check_aws(self, data):
        """Check AWS data at rest encryption"""
        unencrypted_volumes = []
        unencrypted_snapshots = []
        unencrypted_s3_buckets = []
        
        # Check EBS volumes across all regions
        for region, region_data in data.items():
            if 'ec2' in region_data:
                ec2_data = region_data['ec2']
                
                # Check EBS volumes
                volumes = ec2_data.get('volumes', {})
                for volume_id, volume_data in volumes.items():
                    if not volume_data.get('encrypted', False):
                        unencrypted_volumes.append(f"{region}:{volume_id}")
                
                # Check EBS snapshots
                snapshots = ec2_data.get('snapshots', {})
                for snapshot_id, snapshot_data in snapshots.items():
                    if not snapshot_data.get('encrypted', False):
                        unencrypted_snapshots.append(f"{region}:{snapshot_id}")
        
        # Check S3 buckets (S3 is global, check in any region)
        for region, region_data in data.items():
            if 's3' in region_data:
                s3_data = region_data['s3']
                buckets = s3_data.get('buckets', {})
                bucket_encryption = s3_data.get('bucket_encryption', {})
                
                for bucket_name in buckets:
                    if bucket_name not in bucket_encryption or bucket_encryption[bucket_name] is None:
                        unencrypted_s3_buckets.append(bucket_name)
                break  # S3 is global, only check once
        
        # Determine compliance status
        issues = []
        
        if unencrypted_volumes:
            issues.append(f"{len(unencrypted_volumes)} unencrypted EBS volumes")
        
        if unencrypted_snapshots:
            issues.append(f"{len(unencrypted_snapshots)} unencrypted EBS snapshots")
        
        if unencrypted_s3_buckets:
            issues.append(f"{len(unencrypted_s3_buckets)} unencrypted S3 buckets")

        if issues:
            status = "NON_COMPLIANT"
            details = f"Found unencrypted resources: {', '.join(issues)}"
        else:
            status = "COMPLIANT"
            details = "All data at rest is encrypted"

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