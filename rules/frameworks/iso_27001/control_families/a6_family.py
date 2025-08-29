from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.access_control.user_account_management import UserAccountManagementCheck
from rules.checks.access_control.separation_of_duties import SeparationOfDutiesCheck
from rules.checks.access_control.privileged_account import PrivilegedAccountCheck

class A6Family(BaseControlFamily):
    """ISO 27001 A.6 - Organization of Information Security"""
    
    def __init__(self):
        super().__init__(
            family_id="A.6",
            family_name="Organization of Information Security"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize ISO 27001 A.6 controls"""
        controls = [
            # A.6.1.1 - Information Security Roles and Responsibilities
            BaseControl(
                control_id="A.6.1.1",
                control_name="Information Security Roles and Responsibilities",
                checks=[UserAccountManagementCheck()]
            ),
            
            # A.6.1.2 - Segregation of Duties
            BaseControl(
                control_id="A.6.1.2",
                control_name="Segregation of Duties",
                checks=[SeparationOfDutiesCheck()]
            ),
            
            # A.6.1.3 - Contact with Authorities
            BaseControl(
                control_id="A.6.1.3",
                control_name="Contact with Authorities",
                checks=[PrivilegedAccountCheck()]
            ),
            
            # A.6.1.4 - Contact with Special Interest Groups
            BaseControl(
                control_id="A.6.1.4",
                control_name="Contact with Special Interest Groups",
                checks=[PrivilegedAccountCheck()]
            ),
        ]
        
        for control in controls:
            self.add_control(control) 