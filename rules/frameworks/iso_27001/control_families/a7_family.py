from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.user_account_management import UserAccountManagementCheck
from rules.checks.access_control.account_access_review import AccountAccessReviewCheck

class A7Family(BaseControlFamily):
    """ISO 27001 A.7 - Human Resource Security"""
    
    def __init__(self):
        super().__init__(
            family_id="A.7",
            family_name="Human Resource Security"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize ISO 27001 A.7 controls"""
        controls = [
            # A.7.1.1 - Screening
            BaseControl(
                control_id="A.7.1.1",
                control_name="Screening",
                checks=[UserAccountManagementCheck()]
            ),
            
            # A.7.1.2 - Terms and Conditions of Employment
            BaseControl(
                control_id="A.7.1.2",
                control_name="Terms and Conditions of Employment",
                checks=[UserAccountManagementCheck()]
            ),
            
            # A.7.2.1 - Management Responsibilities
            BaseControl(
                control_id="A.7.2.1",
                control_name="Management Responsibilities",
                checks=[AccountAccessReviewCheck()]
            ),
            
            # A.7.2.2 - Information Security Awareness, Education and Training
            BaseControl(
                control_id="A.7.2.2",
                control_name="Information Security Awareness, Education and Training",
                checks=[AccountAccessReviewCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control) 