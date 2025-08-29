from rules.frameworks.base_framework import BaseFramework
from .control_families.ac_family import ACFamily
from .control_families.ia_family import IAFamily
from .control_families.sc_family import SCFamily
from .control_families.au_family import AUFamily
from .control_families.cm_family import CMFamily
from .control_families.si_family import SIFamily
from .control_families.ir_family import IRFamily
from .control_families.ra_family import RAFamily

class NIST80053Framework(BaseFramework):
    """NIST 800-53 Framework - Organizes all control families"""
    
    def __init__(self):
        super().__init__(
            framework_id="nist_800_53",
            framework_name="NIST Special Publication 800-53"
        )
        self.initialize_families()
    
    def initialize_families(self):
        """Initialize all control families for NIST 800-53"""
        self.control_families = [
            ACFamily(),
            IAFamily(),
            SCFamily(),
            AUFamily(),
            CMFamily(),
            SIFamily(),
            IRFamily(),
            RAFamily(),
        ]