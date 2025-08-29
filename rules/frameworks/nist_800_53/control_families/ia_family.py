from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.identification_authentication.mfa_enabled import MFAEnabledCheck
from rules.checks.identification_authentication.password_policy import PasswordPolicyCheck
from rules.checks.identification_authentication.session_authentication import SessionAuthenticationCheck

class IAFamily(BaseControlFamily):
    """Identification and Authentication (IA) Family - All IA controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="IA",
            family_name="Identification and Authentication"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all IA controls"""
        controls = [
            # IA-02: Identification and Authentication
            BaseControl(
                control_id="IA-02",
                control_name="Identification and Authentication",
                checks=[
                    MFAEnabledCheck(),
                    PasswordPolicyCheck(),
                    SessionAuthenticationCheck()
                ]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 