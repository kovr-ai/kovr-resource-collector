from rules.frameworks.base_control_family import BaseControlFamily
from rules.frameworks.base_control import BaseControl
from rules.checks.configuration_management.configuration_settings import ConfigurationSettingsCheck

class CMFamily(BaseControlFamily):
    """Configuration Management (CM) Family - All CM controls grouped together"""
    
    def __init__(self):
        super().__init__(
            family_id="CM",
            family_name="Configuration Management"
        )
        self.initialize_controls()
    
    def initialize_controls(self):
        """Initialize all CM controls"""
        controls = [
            # CM-06: Configuration Settings
            BaseControl(
                control_id="CM-06",
                control_name="Configuration Settings",
                checks=[ConfigurationSettingsCheck()]
            ),
        ]
        
        # Add all controls to the family
        for control in controls:
            self.add_control(control) 