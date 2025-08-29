class PasswordPolicyCheck:
    def check_aws(self, data):
        """Check AWS IAM password policy settings"""
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

        # Get account password policy
        account_data = iam_data.get('account', {})
        password_policy = account_data.get('password_policy', {})
        
        if not password_policy:
            return {
                "status": "NON_COMPLIANT",
                "details": "No password policy found in IAM account data"
            }

        # Check password policy requirements
        policy_issues = []
        policy_indicators = []
        
        # Check if password expiration is enabled
        expire_passwords = password_policy.get('ExpirePasswords', False)
        if not expire_passwords:
            policy_issues.append("Password expiration not enabled")
        else:
            policy_indicators.append("Password expiration enabled")
        
        # Check maximum password age
        max_password_age = password_policy.get('MaxPasswordAge', 0)
        if max_password_age == 0:
            policy_issues.append("No maximum password age set")
        elif max_password_age > 90:
            policy_issues.append(f"Password age too long ({max_password_age} days)")
        else:
            policy_indicators.append(f"Password age: {max_password_age} days")
        
        # Check minimum password length
        min_password_length = password_policy.get('MinimumPasswordLength', 0)
        if min_password_length < 8:
            policy_issues.append(f"Password too short ({min_password_length} characters)")
        else:
            policy_indicators.append(f"Minimum length: {min_password_length} characters")
        
        # Check for password complexity requirements
        require_symbols = password_policy.get('RequireSymbols', False)
        require_numbers = password_policy.get('RequireNumbers', False)
        require_uppercase = password_policy.get('RequireUppercaseCharacters', False)
        require_lowercase = password_policy.get('RequireLowercaseCharacters', False)
        
        complexity_requirements = []
        if require_symbols:
            complexity_requirements.append("symbols")
        if require_numbers:
            complexity_requirements.append("numbers")
        if require_uppercase:
            complexity_requirements.append("uppercase")
        if require_lowercase:
            complexity_requirements.append("lowercase")
        
        if len(complexity_requirements) < 3:
            policy_issues.append(f"Insufficient complexity requirements ({', '.join(complexity_requirements)})")
        else:
            policy_indicators.append(f"Complexity: {', '.join(complexity_requirements)}")
        
        # Check password reuse prevention
        password_reuse_prevention = password_policy.get('PasswordReusePrevention', 0)
        if password_reuse_prevention < 5:
            policy_issues.append(f"Insufficient password reuse prevention ({password_reuse_prevention})")
        else:
            policy_indicators.append(f"Reuse prevention: {password_reuse_prevention}")
        
        # Check for hard expiry
        hard_expiry = password_policy.get('HardExpiry', False)
        if not hard_expiry:
            policy_issues.append("Hard expiry not enabled")
        else:
            policy_indicators.append("Hard expiry enabled")
        
        # Check for allow users to change passwords
        allow_users_to_change_password = password_policy.get('AllowUsersToChangePassword', False)
        if not allow_users_to_change_password:
            policy_issues.append("Users cannot change passwords")
        else:
            policy_indicators.append("Users can change passwords")

        # Determine compliance status
        if policy_issues:
            status = "NON_COMPLIANT"
            details = f"Password policy issues: {', '.join(policy_issues)}"
        elif len(policy_indicators) < 5:
            status = "PARTIAL"
            details = f"Basic password policy configured. {', '.join(policy_indicators)}"
        else:
            status = "COMPLIANT"
            details = f"Strong password policy configured. {', '.join(policy_indicators)}"

        return {
            "status": status,
            "details": details
        }

    def check_google_workspace(self, data):
        # TODO: Implement Google Workspace-specific logic
        return {
            "status": "NOT_IMPLEMENTED",
            "details": "Google Workspace password policy check not implemented"
        } 