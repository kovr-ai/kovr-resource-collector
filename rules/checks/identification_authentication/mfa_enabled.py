class MFAEnabledCheck:
    def check_aws(self, data):
        """Check AWS MFA configuration for users and roles"""
        users_without_mfa = []
        users_with_console_access = []
        privileged_users_without_mfa = []
        
        # Find IAM data in any region (IAM is global)
        iam_data = None
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

        for user_id, user_data in users.items():
            # Check if user has console access
            login_profile = user_data.get('login_profile')
            if login_profile:
                users_with_console_access.append(user_id)
                
                # Check MFA for console users
                mfa_devices = user_data.get('mfa_devices', [])
                if not mfa_devices:
                    users_without_mfa.append(user_id)
                    
                    # Check if user has privileged access (admin policies)
                    user_policies = iam_data.get('relationships', {}).get('user_policies', {}).get(user_id, {})
                    attached_policies = user_policies.get('attached', [])
                    
                    # Check for admin policies
                    admin_policies = [
                        'arn:aws:iam::aws:policy/AdministratorAccess',
                        'arn:aws:iam::aws:policy/PowerUserAccess',
                        'arn:aws:iam::aws:policy/SystemAdministrator'
                    ]
                    
                    for policy in attached_policies:
                        if any(admin_policy in policy for admin_policy in admin_policies):
                            privileged_users_without_mfa.append(user_id)
                            break

        # Determine compliance status
        if privileged_users_without_mfa:
            status = "NON_COMPLIANT"
            details = f"Found {len(privileged_users_without_mfa)} privileged users without MFA"
        elif users_without_mfa:
            status = "PARTIAL"
            details = f"Found {len(users_without_mfa)} console users without MFA"
        else:
            status = "COMPLIANT"
            details = f"All {len(users_with_console_access)} console users have MFA enabled"

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