class SessionAuthenticationCheck:
    def check_aws(self, data):
        """Check AWS session authentication and temporary credentials"""
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
                "details": "No IAM users found for session authentication analysis"
            }

        users_with_active_sessions = []
        users_with_old_sessions = []
        users_without_session_timeout = []
        users_with_console_access = []

        for user_id, user_data in users.items():
            if user_data.get('status') != 'Active':
                continue

            # Check for console access (indicates potential session usage)
            login_profile = user_data.get('login_profile')
            if login_profile:
                users_with_console_access.append(user_id)

            # Check access keys (temporary credentials)
            access_keys = user_data.get('access_keys', [])
            if access_keys:
                for key in access_keys:
                    if key.get('Status') == 'Active':
                        users_with_active_sessions.append(user_id)
                        
                        # Check for old access keys (older than 90 days)
                        import datetime
                        from datetime import timezone
                        now = datetime.datetime.now(timezone.utc)
                        
                        create_date = key.get('CreateDate')
                        if create_date:
                            if isinstance(create_date, str):
                                create_date = datetime.datetime.fromisoformat(create_date.replace('Z', '+00:00'))
                            age_days = (now - create_date).days
                            if age_days > 90:
                                users_with_old_sessions.append(user_id)

        # Check account password policy for session timeout settings
        account_data = iam_data.get('account', {})
        password_policy = account_data.get('password_policy', {})
        
        # Check for session timeout settings in password policy
        if not password_policy.get('ExpirePasswords') or not password_policy.get('MaxPasswordAge'):
            users_without_session_timeout.append('account_level')

        # Determine compliance status
        issues = []
        
        if users_with_old_sessions:
            issues.append(f"{len(users_with_old_sessions)} users with old access keys (>90 days)")
        
        if users_without_session_timeout:
            issues.append("No password expiration policy configured")
        
        if not users_with_console_access and not users_with_active_sessions:
            issues.append("No active sessions or console access found")

        if issues:
            status = "NON_COMPLIANT"
            details = f"Session authentication issues: {', '.join(issues)}"
        elif users_with_old_sessions:
            status = "PARTIAL"
            details = f"Found {len(users_with_active_sessions)} users with active sessions, {len(users_with_old_sessions)} with old sessions"
        else:
            status = "COMPLIANT"
            details = f"Found {len(users_with_active_sessions)} users with active sessions, all properly managed"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace session authentication check not implemented"
        } 