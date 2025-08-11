from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.risk_assessment.vulnerability_scanning import VulnerabilityScanningCheck

class RAFamily(BaseControlFamily):
    """Risk Assessment (RA) Family - All RA controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="RA",
            family_name="Risk Assessment"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all RA controls"""
        controls = [
            # RA-05: Vulnerability Scanning
            BaseControl(
                control_id="RA-05",
                control_name="Vulnerability Scanning",
                checks=[VulnerabilityScanningCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 