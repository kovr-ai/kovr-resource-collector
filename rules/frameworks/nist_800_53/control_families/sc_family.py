from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.system_communications_protection.boundary_protection import BoundaryProtectionCheck
from rules.checks.system_communications_protection.transmission_confidentiality import TransmissionConfidentialityCheck
from rules.checks.system_communications_protection.cryptographic_protection import CryptographicProtectionCheck
from rules.checks.encryption.data_at_rest import DataAtRestEncryptionCheck
from rules.checks.audit.logging_enabled import LoggingEnabledCheck

class SCFamily(BaseControlFamily):
    """System and Communications Protection (SC) Family - All SC controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="SC",
            family_name="System and Communications Protection"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all SC controls"""
        controls = [
            # SC-07: Boundary Protection
            BaseControl(
                control_id="SC-07",
                control_name="Boundary Protection",
                checks=[BoundaryProtectionCheck()]
            ),
            
            # SC-08: Transmission Confidentiality and Integrity
            BaseControl(
                control_id="SC-08",
                control_name="Transmission Confidentiality and Integrity",
                checks=[TransmissionConfidentialityCheck()]
            ),
            
            # SC-13: Cryptographic Protection
            BaseControl(
                control_id="SC-13",
                control_name="Cryptographic Protection",
                checks=[CryptographicProtectionCheck()]
            ),
            
            # SC-28: Protection of Information at Rest
            BaseControl(
                control_id="SC-28",
                control_name="Protection of Information at Rest",
                checks=[
                    DataAtRestEncryptionCheck(),
                    LoggingEnabledCheck()
                ]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 