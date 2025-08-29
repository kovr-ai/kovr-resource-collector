class UserAccountManagementCheck:
    def check_aws(self, data):
        """Check AWS IAM user account management"""
        iam_data = None
        
        # Find IAM data in any region (IAM is global)
        for region, region_data in data.items():
            if 'iam' in region_data:
                iam_data = region_data['iam']
                break

        if not iam_data:
            return {
                "status": "NON_COMPLIANT",
                "details": "No IAM data found in collected AWS data"
            }

        users = iam_data.get('users', {})
        if not users:
            return {
                "status": "NON_COMPLIANT",
                "details": "No IAM users found"
            }

        active_users = []
        inactive_users = []
        users_without_mfa = []
        users_with_access_keys = []
        users_with_console_access = []
        users_with_old_access_keys = []

        for user_id, user_data in users.items():
            # Check if user is active
            if user_data.get('status') == 'Active':
                active_users.append(user_id)
                
                # Check MFA
                mfa_devices = user_data.get('mfa_devices', [])
                if not mfa_devices:
                    users_without_mfa.append(user_id)
                
                # Check access keys
                access_keys = user_data.get('access_keys', [])
                if access_keys:
                    users_with_access_keys.append(user_id)
                    
                    # Check for old access keys (older than 90 days)
                    import datetime
                    from datetime import timezone
                    now = datetime.datetime.now(timezone.utc)
                    
                    for key in access_keys:
                        if key.get('Status') == 'Active':
                            create_date = key.get('CreateDate')
                            if create_date:
                                if isinstance(create_date, str):
                                    create_date = datetime.datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                                age_days = (now - create_date).days
                                if age_days > 90:
                                    users_with_old_access_keys.append(user_id)
                                    break
                
                # Check console access
                login_profile = user_data.get('login_profile')
                if login_profile:
                    users_with_console_access.append(user_id)
            else:
                inactive_users.append(user_id)

        # Determine compliance status
        issues = []
        
        if users_without_mfa:
            issues.append(f"{len(users_without_mfa)} users without MFA")
        
        if users_with_old_access_keys:
            issues.append(f"{len(users_with_old_access_keys)} users with old access keys (>90 days)")
        
        if inactive_users:
            issues.append(f"{len(inactive_users)} inactive users")

        if issues:
            status = "NON_COMPLIANT"
            details = f"Found {len(active_users)} active users. Issues: {', '.join(issues)}"
        elif inactive_users:
            status = "PARTIAL"
            details = f"Found {len(active_users)} active users, {len(inactive_users)} inactive users"
        else:
            status = "COMPLIANT"
            details = f"Found {len(active_users)} active users, all properly configured"

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