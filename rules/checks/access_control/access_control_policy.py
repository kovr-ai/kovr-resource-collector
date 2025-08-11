class AccessControlPolicyCheck:
    def check_aws(self, data):
        """Check AWS access control policy verification"""
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

        # Check for documented policies
        policies = iam_data.get('policies', {})
        users = iam_data.get('users', {})
        groups = iam_data.get('groups', {})
        roles = iam_data.get('roles', {})
        
        # Check account summary for policy compliance
        account_data = iam_data.get('account', {})
        account_summary = account_data.get('summary', {})
        
        # Define policy compliance checks
        policy_issues = []
        compliance_indicators = []
        
        # Check for managed policies (indicates documented approach)
        if policies:
            managed_policies = [p for p in policies.values() if p.get('path', '').startswith('/aws-service-role/') or p.get('path', '').startswith('/service-role/')]
            custom_policies = [p for p in policies.values() if not p.get('path', '').startswith('/aws-service-role/') and not p.get('path', '').startswith('/service-role/')]
            
            if custom_policies:
                compliance_indicators.append(f"{len(custom_policies)} custom policies defined")
            else:
                policy_issues.append("No custom policies found")
        else:
            policy_issues.append("No IAM policies found")
        
        # Check for users with policies (indicates access control implementation)
        users_with_policies = 0
        users_without_policies = 0
        
        for user_id, user_data in users.items():
            if user_data.get('status') == 'Active':
                # Check if user has any policies attached
                has_policies = False
                
                # Check relationships for policy attachments
                relationships = iam_data.get('relationships', {})
                user_policies = relationships.get('user_policies', {}).get(user_id, {})
                
                if user_policies.get('inline') or user_policies.get('attached'):
                    has_policies = True
                
                # Check group memberships
                user_groups = relationships.get('user_groups', {}).get(user_id, [])
                for group_name in user_groups:
                    group_policies = relationships.get('group_policies', {}).get(group_name, {})
                    if group_policies.get('inline') or group_policies.get('attached'):
                        has_policies = True
                        break
                
                if has_policies:
                    users_with_policies += 1
                else:
                    users_without_policies += 1
        
        # Check for roles with policies
        roles_with_policies = 0
        for role_id, role_data in roles.items():
            relationships = iam_data.get('relationships', {})
            role_policies = relationships.get('role_policies', {}).get(role_id, {})
            
            if role_policies.get('inline') or role_policies.get('attached'):
                roles_with_policies += 1
        
        # Check for groups (indicates organizational structure)
        if groups:
            compliance_indicators.append(f"{len(groups)} groups defined")
        else:
            policy_issues.append("No IAM groups found")
        
        # Check for roles (indicates service-to-service access control)
        if roles:
            compliance_indicators.append(f"{len(roles)} roles defined")
        else:
            policy_issues.append("No IAM roles found")
        
        # Determine compliance status
        if policy_issues:
            status = "NON_COMPLIANT"
            details = f"Access control policy issues: {', '.join(policy_issues)}"
        elif users_without_policies > 0:
            status = "PARTIAL"
            details = f"Found {users_with_policies} users with policies, {users_without_policies} without policies. {', '.join(compliance_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"All {users_with_policies} active users have policies. {', '.join(compliance_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace access control policy check not implemented"
        } 