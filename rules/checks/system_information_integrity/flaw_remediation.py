class FlawRemediationCheck:
    def check_aws(self, data):
        """Check AWS flaw remediation and security patch management"""
        cloudwatch_data = None
        cloudtrail_data = None
        ec2_data = {}
        
        # Find relevant data across regions
        for region, region_data in data.items():
            if 'cloudwatch' in region_data:
                cloudwatch_data = region_data['cloudwatch']
            if 'cloudtrail' in region_data and not cloudtrail_data:
                cloudtrail_data = region_data['cloudtrail']
            if 'ec2' in region_data:
                ec2_data[region] = region_data['ec2']

        if not cloudwatch_data and not cloudtrail_data and not ec2_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No AWS data found for flaw remediation analysis"
            }

        # Analyze flaw remediation capabilities
        remediation_indicators = []
        remediation_issues = []
        
        # Check CloudWatch for monitoring and alerting
        if cloudwatch_data:
            alarms = cloudwatch_data.get('alarms', {})
            log_groups = cloudwatch_data.get('log_groups', {})
            metrics = cloudwatch_data.get('metrics', {})
            
            # Check for security-related alarms
            security_alarms = []
            for alarm_name, alarm_data in alarms.items():
                alarm_description = alarm_data.get('alarm_description', '').lower()
                if any(keyword in alarm_description for keyword in ['vulnerability', 'patch', 'update', 'security', 'flaw']):
                    security_alarms.append(alarm_name)
            
            if security_alarms:
                remediation_indicators.append(f"{len(security_alarms)} security monitoring alarms")
            else:
                remediation_issues.append("No security monitoring alarms found")
            
            # Check for security-related log groups
            security_log_groups = []
            for log_group_name in log_groups.keys():
                if any(keyword in log_group_name.lower() for keyword in ['security', 'vulnerability', 'patch', 'update', 'system']):
                    security_log_groups.append(log_group_name)
            
            if security_log_groups:
                remediation_indicators.append(f"{len(security_log_groups)} security-related log groups")
            else:
                remediation_issues.append("No security-related log groups found")
            
            # Check for metrics (indicates monitoring infrastructure)
            if metrics:
                metric_count = sum(len(metric_list) for metric_list in metrics.values())
                remediation_indicators.append(f"{metric_count} CloudWatch metrics for monitoring")
            else:
                remediation_issues.append("No CloudWatch metrics found")
        
        # Check CloudTrail for security event tracking
        if cloudtrail_data:
            trails = cloudtrail_data.get('trails', {})
            
            # Check for comprehensive logging
            trails_with_global_events = [trail for trail in trails.values() if trail.get('include_global_service_events', False)]
            if trails_with_global_events:
                remediation_indicators.append(f"{len(trails_with_global_events)} trails with global service events")
            else:
                remediation_issues.append("No CloudTrail trails with global service events")
            
            # Check for log file validation
            trails_with_validation = [trail for trail in trails.values() if trail.get('log_file_validation_enabled', False)]
            if trails_with_validation:
                remediation_indicators.append(f"{len(trails_with_validation)} trails with log file validation")
            else:
                remediation_issues.append("No CloudTrail log file validation")
            
            # Check for S3 logging
            trails_with_logging = [trail for trail in trails.values() if trail.get('s3_bucket_name')]
            if trails_with_logging:
                remediation_indicators.append(f"{len(trails_with_logging)} trails with S3 logging")
            else:
                remediation_issues.append("No CloudTrail S3 logging configured")
        
        # Check EC2 for system management
        if ec2_data:
            total_instances = 0
            instances_with_security_groups = 0
            instances_with_iam_roles = 0
            
            for region, region_ec2 in ec2_data.items():
                instances = region_ec2.get('instances', {})
                
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
                        
                    #     # Check for IAM roles (indicates proper access management)
                    #     iam_instance_profile = instance_data.get('iam_instance_profile')
                    #     if iam_instance_profile:
                    #         instances_with_iam_roles += 1
            
            if total_instances > 0:
                remediation_indicators.append(f"{total_instances} EC2 instances")
                
                if instances_with_security_groups > 0:
                    remediation_indicators.append(f"{instances_with_security_groups} instances with security groups")
                else:
                    remediation_issues.append("No instances with security groups")
                
                if instances_with_iam_roles > 0:
                    remediation_indicators.append(f"{instances_with_iam_roles} instances with IAM roles")
                else:
                    remediation_issues.append("No instances with IAM roles")
            else:
                remediation_indicators.append("No EC2 instances found")
        
        # Check for Systems Manager or similar management tools
        # This would typically be detected through CloudTrail events or specific service data
        # For now, we'll check if there are any management-related log groups
        if cloudwatch_data:
            log_groups = cloudwatch_data.get('log_groups', {})
            management_log_groups = []
            for log_group_name in log_groups.keys():
                if any(keyword in log_group_name.lower() for keyword in ['ssm', 'systems-manager', 'patch', 'update', 'maintenance']):
                    management_log_groups.append(log_group_name)
            
            if management_log_groups:
                remediation_indicators.append(f"{len(management_log_groups)} management-related log groups")
            else:
                remediation_issues.append("No management-related log groups found")

        # Determine compliance status
        if remediation_issues:
            status = "NON_COMPLIANT"
            details = f"Flaw remediation issues: {', '.join(remediation_issues)}"
        elif len(remediation_indicators) < 4:
            status = "PARTIAL"
            details = f"Basic flaw remediation capabilities. {', '.join(remediation_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive flaw remediation capabilities. {', '.join(remediation_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace flaw remediation check not implemented"
        } 