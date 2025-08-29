class AuditEventsCheck:
    def check_aws(self, data):
        """Check AWS audit events and CloudTrail configuration"""
        cloudtrail_data = None
        
        # Find CloudTrail data in any region
        for region, region_data in data.items():
            if 'cloudtrail' in region_data:
                cloudtrail_data = region_data['cloudtrail']
                break

        if not cloudtrail_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No CloudTrail data found in collected AWS data"
            }

        trails = cloudtrail_data.get('trails', {})
        if not trails:
            return {
                "status": "NON_COMPLIANT",
                "details": "No CloudTrail trails found"
            }

        # Analyze trail configurations
        multi_region_trails = []
        trails_with_logging = []
        trails_with_encryption = []
        trails_with_validation = []
        trails_with_insights = []
        trails_with_global_events = []
        
        for trail_name, trail_data in trails.items():
            # Check for multi-region trails
            if trail_data.get('is_multi_region_trail', False):
                multi_region_trails.append(trail_name)
            
            # Check for S3 logging
            if trail_data.get('s3_bucket_name'):
                trails_with_logging.append(trail_name)
            
            # Check for KMS encryption
            if trail_data.get('kms_key_id'):
                trails_with_encryption.append(trail_name)
            
            # Check for log file validation
            if trail_data.get('log_file_validation_enabled', False):
                trails_with_validation.append(trail_name)
            
            # Check for CloudTrail Insights
            if trail_data.get('has_insight_selectors', False):
                trails_with_insights.append(trail_name)
            
            # Check for global service events
            if trail_data.get('include_global_service_events', False):
                trails_with_global_events.append(trail_name)

        # Check event selectors for comprehensive logging
        event_selectors = cloudtrail_data.get('event_selectors', {})
        trails_with_read_write = []
        trails_with_management_events = []
        
        for trail_name, selectors in event_selectors.items():
            for selector in selectors:
                # Check for read/write events
                read_write_type = selector.get('ReadWriteType', '')
                if read_write_type in ['All', 'WriteOnly']:
                    trails_with_read_write.append(trail_name)
                
                # Check for management events
                include_management_events = selector.get('IncludeManagementEvents', True)
                if include_management_events:
                    trails_with_management_events.append(trail_name)

        # Determine compliance status
        issues = []
        compliance_indicators = []
        
        if not multi_region_trails:
            issues.append("No multi-region trails found")
        else:
            compliance_indicators.append(f"{len(multi_region_trails)} multi-region trails")
        
        if not trails_with_logging:
            issues.append("No trails with S3 logging configured")
        else:
            compliance_indicators.append(f"{len(trails_with_logging)} trails with S3 logging")
        
        if not trails_with_encryption:
            issues.append("No trails with KMS encryption")
        else:
            compliance_indicators.append(f"{len(trails_with_encryption)} trails with KMS encryption")
        
        if not trails_with_validation:
            issues.append("No trails with log file validation")
        else:
            compliance_indicators.append(f"{len(trails_with_validation)} trails with log validation")
        
        if not trails_with_global_events:
            issues.append("No trails with global service events")
        else:
            compliance_indicators.append(f"{len(trails_with_global_events)} trails with global events")

        if issues:
            status = "NON_COMPLIANT"
            details = f"Audit event issues: {', '.join(issues)}"
        elif len(compliance_indicators) < 3:
            status = "PARTIAL"
            details = f"Basic audit logging configured. {', '.join(compliance_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Comprehensive audit logging configured. {', '.join(compliance_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace audit events check not implemented"
        } 