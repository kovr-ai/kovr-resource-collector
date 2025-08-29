from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.access_enforcement import AccessEnforcementCheck
from rules.checks.access_control.least_privilege import LeastPrivilegeCheck
from rules.checks.access_control.remote_access import RemoteAccessCheck
from rules.checks.identification_authentication.mfa_enabled import MFAEnabledCheck

class A9Family(BaseControlFamily):
    """ISO 27001 A.9 - Access Control"""
    
    def __init__(self):
        super().__init__(
            family_id="A.9",
            family_name="Access Control"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize ISO 27001 A.9 controls"""
        controls = [
            # A.9.1.1 - Access Control Policy
            BaseControl(
                control_id="A.9.1.1",
                control_name="Access Control Policy",
                checks=[AccessEnforcementCheck()]
            ),
            
            # A.9.1.2 - Access to Networks and Network Services
            BaseControl(
                control_id="A.9.1.2",
                control_name="Access to Networks and Network Services",
                checks=[RemoteAccessCheck()]
            ),
            
            # A.9.2.1 - User Registration and De-registration
            BaseControl(
                control_id="A.9.2.1",
                control_name="User Registration and De-registration",
                checks=[AccessEnforcementCheck()]
            ),
            
            # A.9.2.2 - User Access Provisioning
            BaseControl(
                control_id="A.9.2.2",
                control_name="User Access Provisioning",
                checks=[LeastPrivilegeCheck()]
            ),
            
            # A.9.2.3 - Access Rights Management
            BaseControl(
                control_id="A.9.2.3",
                control_name="Access Rights Management",
                checks=[LeastPrivilegeCheck()]
            ),
            
            # A.9.3.1 - Use of Secret Authentication Information
            BaseControl(
                control_id="A.9.3.1",
                control_name="Use of Secret Authentication Information",
                checks=[MFAEnabledCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control) 