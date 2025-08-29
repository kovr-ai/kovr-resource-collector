from rules.frameworks.base_framework import BaseFramework
from .control_families.a5_family import A5Family
from .control_families.a6_family import A6Family
from .control_families.a7_family import A7Family
from .control_families.a9_family import A9Family

class ISO27001Framework(BaseFramework):
    """ISO 27001 Framework - Information Security Management"""
    
    def __init__(self):
        super().__init__(
            framework_id="iso_27001",
            framework_name="ISO/IEC 27001 Information Security Management"
        )
        self.initialize_families()
    
    def initialize_families(self):
        """Initialize all ISO 27001 control families"""
        self.control_families = [
            A5Family(),
            A6Family(),
            A7Family(),
            A9Family(),
        ] 