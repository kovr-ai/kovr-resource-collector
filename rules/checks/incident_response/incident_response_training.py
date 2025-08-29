class IncidentResponseTrainingCheck:
    def check_aws(self, data):
        """Check AWS incident response capabilities and monitoring"""
        cloudwatch_data = None
        cloudtrail_data = None
        iam_data = None
        
        # Find relevant data across regions
        for region, region_data in data.items():
            if 'cloudwatch' in region_data:
                cloudwatch_data = region_data['cloudwatch']
            if 'cloudtrail' in region_data:
                cloudtrail_data = region_data['cloudtrail']
            if 'iam' in region_data and not iam_data:
                iam_data = region_data['iam']

        if not cloudwatch_data and not cloudtrail_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No CloudWatch or CloudTrail data found for incident response analysis"
            }

        # Analyze incident response capabilities
        response_indicators = []
        response_issues = []
        
        # Check CloudWatch monitoring capabilities
        if cloudwatch_data:
            alarms = cloudwatch_data.get('alarms', {})
            log_groups = cloudwatch_data.get('log_groups', {})
            metrics = cloudwatch_data.get('metrics', {})
            
            # Check for security-related alarms
            security_alarms = []
            for alarm_name, alarm_data in alarms.items():
                alarm_description = alarm_data.get('alarm_description', '').lower()
                if any(keyword in alarm_description for keyword in ['security', 'breach', 'unauthorized', 'failed', 'error']):
                    security_alarms.append(alarm_name)
            
            if security_alarms:
                response_indicators.append(f"{len(security_alarms)} security-related alarms")
            else:
                response_issues.append("No security-related alarms found")
            
            # Check for log groups (indicates logging infrastructure)
            if log_groups:
                response_indicators.append(f"{len(log_groups)} CloudWatch log groups")
            else:
                response_issues.append("No CloudWatch log groups found")
            
            # Check for metrics (indicates monitoring)
            if metrics:
                metric_count = sum(len(metric_list) for metric_list in metrics.values())
                response_indicators.append(f"{metric_count} CloudWatch metrics")
            else:
                response_issues.append("No CloudWatch metrics found")
        
        # Check CloudTrail for audit trail capabilities
        if cloudtrail_data:
            trails = cloudtrail_data.get('trails', {})
            
            # Check for multi-region trails
            multi_region_trails = [trail for trail in trails.values() if trail.get('is_multi_region_trail', False)]
            if multi_region_trails:
                response_indicators.append(f"{len(multi_region_trails)} multi-region CloudTrail trails")
            else:
                response_issues.append("No multi-region CloudTrail trails found")
            
            # Check for CloudTrail Insights
            trails_with_insights = [trail for trail in trails.values() if trail.get('has_insight_selectors', False)]
            if trails_with_insights:
                response_indicators.append(f"{len(trails_with_insights)} trails with CloudTrail Insights")
            else:
                response_issues.append("No CloudTrail Insights configured")
            
            # Check for S3 logging
            trails_with_logging = [trail for trail in trails.values() if trail.get('s3_bucket_name')]
            if trails_with_logging:
                response_indicators.append(f"{len(trails_with_logging)} trails with S3 logging")
            else:
                response_issues.append("No CloudTrail S3 logging configured")
        
        # Check IAM for access monitoring
        if iam_data:
            users = iam_data.get('users', {})
            active_users = [user for user in users.values() if user.get('status') == 'Active']
            
            if active_users:
                response_indicators.append(f"{len(active_users)} active IAM users for monitoring")
            else:
                response_issues.append("No active IAM users found")
            
            # Check for MFA on users
            users_with_mfa = [user for user in active_users if user.get('mfa_devices')]
            if users_with_mfa:
                response_indicators.append(f"{len(users_with_mfa)} users with MFA")
            else:
                response_issues.append("No users with MFA found")

        # Determine compliance status
        if response_issues:
            status = "NON_COMPLIANT"
            details = f"Incident response issues: {', '.join(response_issues)}"
        elif len(response_indicators) < 4:
            status = "PARTIAL"
            details = f"Basic incident response capabilities. {', '.join(response_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive incident response capabilities. {', '.join(response_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace incident response training check not implemented"
        } 