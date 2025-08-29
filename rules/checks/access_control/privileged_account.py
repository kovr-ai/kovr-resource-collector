class PrivilegedAccountCheck:
    def check_aws(self, data):
        # Look for IAM data in the collected AWS data
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
                "details": "No IAM users found for privileged account analysis"
            }
        
        # Define privileged policy patterns
        privileged_policies = [
            'AdministratorAccess',
            'PowerUserAccess',
            'SystemAdministrator',
            'FullAccess',
            'SuperUser',
            'RootAccess'
        ]
        
        privileged_users = []
        users_without_mfa = []
        users_with_direct_policies = []
        
        for user_id, user_data in users.items():
            if user_data.get('status') != 'Active':
                continue
            
            is_privileged = False
            
            # Check attached policies
            attached_policies = user_data.get('attached_policies', [])
            for policy in attached_policies:
                policy_name = policy.get('policy_name', '')
                if any(priv in policy_name for priv in privileged_policies):
                    is_privileged = True
                    break
            
            # Check inline policies
            inline_policies = user_data.get('inline_policies', [])
            for policy in inline_policies:
                policy_name = policy.get('policy_name', '')
                if any(priv in policy_name for priv in privileged_policies):
                    is_privileged = True
                    break
            
            # Check groups
            groups = user_data.get('groups', [])
            for group in groups:
                group_name = group.get('group_name', '')
                if any(priv in group_name for priv in privileged_policies):
                    is_privileged = True
                    break
            
            if is_privileged:
                privileged_users.append(user_id)
                
                # Check if privileged user has MFA
                if not user_data.get('mfa_devices'):
                    users_without_mfa.append(user_id)
                
                # Check for direct policy attachments (not recommended)
                if attached_policies or inline_policies:
                    users_with_direct_policies.append(user_id)
        
        # Determine compliance status
        if users_without_mfa:
            status = "NON_COMPLIANT"
        elif users_with_direct_policies:
            status = "PARTIAL"
        else:
            status = "COMPLIANT"
        
        return {
            "status": status,
            "details": f"Found {len(privileged_users)} privileged users, {len(users_without_mfa)} without MFA"
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace check not implemented"
        } 