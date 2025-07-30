class LoggingEnabledCheck:
    def check_aws(self, data):
        """Check AWS logging and monitoring configuration"""
        cloudtrail_issues = []
        cloudwatch_issues = []
        s3_logging_issues = []
        
        # Check CloudTrail configuration (global service)
        cloudtrail_enabled = False
        for region, region_data in data.items():
            if 'cloudtrail' in region_data:
                cloudtrail_data = region_data['cloudtrail']
                trails = cloudtrail_data.get('trails', {})
                
                for trail_name, trail_data in trails.items():
                    # Check if trail is enabled and properly configured
                    if trail_data.get('s3_bucket_name'):
                        cloudtrail_enabled = True
                        
                        # Check for additional logging features
                        if not trail_data.get('log_file_validation_enabled', False):
                            cloudtrail_issues.append(f"Log file validation disabled for trail {trail_name}")
                        
                        if not trail_data.get('include_global_service_events', False):
                            cloudtrail_issues.append(f"Global service events not included for trail {trail_name}")
                        
                        if not trail_data.get('is_multi_region_trail', False):
                            cloudtrail_issues.append(f"Trail {trail_name} is not multi-region")
                
                break  # CloudTrail is global, only check once
        
        if not cloudtrail_enabled:
            cloudtrail_issues.append("No CloudTrail trails configured")
        
        # Check CloudWatch Logs configuration
        for region, region_data in data.items():
            if 'cloudwatch' in region_data:
                cloudwatch_data = region_data['cloudwatch']
                log_groups = cloudwatch_data.get('log_groups', {})
                
                if not log_groups:
                    cloudwatch_issues.append(f"No CloudWatch Log Groups in {region}")
                else:
                    # Check for specific log groups that should exist
                    required_log_groups = [
                        '/aws/cloudtrail/',
                        '/aws/vpc/flowlogs/',
                        '/aws/rds/instance/'
                    ]
                    
                    for required_group in required_log_groups:
                        found = False
                        for log_group_name in log_groups:
                            if required_group in log_group_name:
                                found = True
                                break
                        if not found:
                            cloudwatch_issues.append(f"Missing required log group pattern: {required_group}")
        
        # Check S3 bucket logging
        for region, region_data in data.items():
            if 's3' in region_data:
                s3_data = region_data['s3']
                buckets = s3_data.get('buckets', {})
                bucket_logging = s3_data.get('bucket_logging', {})
                
                for bucket_name in buckets:
                    if bucket_name not in bucket_logging or bucket_logging[bucket_name] is None:
                        s3_logging_issues.append(f"S3 bucket {bucket_name} has no logging configured")
                break  # S3 is global, only check once
        
        # Determine compliance status
        all_issues = cloudtrail_issues + cloudwatch_issues + s3_logging_issues
        
        if all_issues:
            status = "NON_COMPLIANT"
            details = f"Logging issues found: {', '.join(all_issues[:3])}"  # Show first 3 issues
            if len(all_issues) > 3:
                details += f" and {len(all_issues) - 3} more"
        else:
            status = "COMPLIANT"
            details = "All logging and monitoring is properly configured"

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