class AccountAccessReviewCheck:
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
                "details": "No IAM users found for access review"
            }
        
        # Analyze access patterns
        users_needing_review = []
        users_with_old_access = []
        users_with_excessive_permissions = []
        
        for user_id, user_data in users.items():
            if user_data.get('status') != 'Active':
                continue
                
            # Check last activity (if available)
            last_activity = user_data.get('password_last_used')
            if last_activity:
                # Simple check - if password used more than 90 days ago, needs review
                from datetime import datetime, timedelta
                try:
                    last_used = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    if datetime.now(last_used.tzinfo) - last_used > timedelta(days=90):
                        users_with_old_access.append(user_id)
                except:
                    pass
            
            # Check for excessive permissions
            attached_policies = user_data.get('attached_policies', [])
            inline_policies = user_data.get('inline_policies', [])
            groups = user_data.get('groups', [])
            
            total_policies = len(attached_policies) + len(inline_policies) + len(groups)
            if total_policies > 5:  # Arbitrary threshold
                users_with_excessive_permissions.append(user_id)
            
            # Add to review list if any issues
            if user_id in users_with_old_access or user_id in users_with_excessive_permissions:
                users_needing_review.append(user_id)
        
        # Determine compliance status
        if users_needing_review:
            status = "NON_COMPLIANT"
        else:
            status = "COMPLIANT"
        
        return {
            "status": status,
            "details": f"Found {len(users_needing_review)} users needing access review"
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace check not implemented"
        } 