from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.system_information_integrity.flaw_remediation import FlawRemediationCheck

class SIFamily(BaseControlFamily):
    """System and Information Integrity (SI) Family - All SI controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="SI",
            family_name="System and Information Integrity"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all SI controls"""
        controls = [
            # SI-02: Flaw Remediation
            BaseControl(
                control_id="SI-02",
                control_name="Flaw Remediation",
                checks=[FlawRemediationCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 