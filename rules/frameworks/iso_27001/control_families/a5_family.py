from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.access_control_policy import AccessControlPolicyCheck
from rules.checks.access_control.user_account_management import UserAccountManagementCheck

class A5Family(BaseControlFamily):
    """ISO 27001 A.5 - Information Security Policies"""
    
    def __init__(self):
        super().__init__(
            family_id="A.5",
            family_name="Information Security Policies"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize ISO 27001 A.5 controls"""
        controls = [
            # A.5.1.1 - Information Security Policy
            BaseControl(
                control_id="A.5.1.1",
                control_name="Information Security Policy",
                checks=[AccessControlPolicyCheck()]
            ),
            
            # A.5.1.2 - Review of Information Security Policy
            BaseControl(
                control_id="A.5.1.2",
                control_name="Review of Information Security Policy",
                checks=[AccessControlPolicyCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control) 