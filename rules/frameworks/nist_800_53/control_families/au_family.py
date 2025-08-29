from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.audit.audit_events import AuditEventsCheck
from rules.checks.audit.audit_review import AuditReviewCheck

class AUFamily(BaseControlFamily):
    """Audit and Accountability (AU) Family - All AU controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="AU",
            family_name="Audit and Accountability"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all AU controls"""
        controls = [
            # AU-02: Audit Events
            BaseControl(
                control_id="AU-02",
                control_name="Audit Events",
                checks=[AuditEventsCheck()]
            ),
            
            # AU-06: Audit Review, Analysis, and Reporting
            BaseControl(
                control_id="AU-06",
                control_name="Audit Review, Analysis, and Reporting",
                checks=[AuditReviewCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 