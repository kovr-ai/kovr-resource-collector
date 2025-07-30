from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.incident_response.incident_response_training import IncidentResponseTrainingCheck

class IRFamily(BaseControlFamily):
    """Incident Response (IR) Family - All IR controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="IR",
            family_name="Incident Response"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all IR controls"""
        controls = [
            # IR-04: Incident Response Training
            BaseControl(
                control_id="IR-04",
                control_name="Incident Response Training",
                checks=[IncidentResponseTrainingCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 