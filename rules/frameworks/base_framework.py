from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseFramework(ABC):
    """Base class for all compliance frameworks"""
    
    def __init__(self, framework_id: str, framework_name: str):
        self.framework_id = framework_id
        self.framework_name = framework_name
        self.control_families = []
    
    @abstractmethod
    def initialize_families(self):
        """Initialize control families for this framework - must be implemented by subclasses"""
        pass
    
    def get_all_controls(self) -> List:
        """Return all controls from all families"""
        all_controls = []
        for family in self.control_families:
            all_controls.extend(family.get_controls())
        return all_controls
    
    def get_control_by_id(self, control_id: str):
        """Get a specific control by ID across all families"""
        for family in self.control_families:
            control = family.get_control_by_id(control_id)
            if control:
                return control
        return None
    
    def get_family_by_id(self, family_id: str):
        """Get a specific control family by ID"""
        for family in self.control_families:
            if family.family_id == family_id:
                return family
        return None
    
    def get_family_summary(self) -> Dict[str, Any]:
        """Get summary of all control families"""
        summary = {
            "framework_id": self.framework_id,
            "framework_name": self.framework_name,
            "total_controls": len(self.get_all_controls()),
            "families": []
        }
        
        for family in self.control_families:
            family_summary = {
                "family_id": family.family_id,
                "family_name": family.family_name,
                "control_count": len(family.get_controls()),
                "controls": [ctrl.control_id for ctrl in family.get_controls()]
            }
            summary["families"].append(family_summary)
        
        return summary
    
    def get_controls_by_family(self, family_id: str) -> List:
        """Get all controls for a specific family"""
        family = self.get_family_by_id(family_id)
        if family:
            return family.get_controls()
        return []
    
    def get_control_count(self) -> int:
        """Get total number of controls"""
        return len(self.get_all_controls())
    
    def get_family_count(self) -> int:
        """Get total number of control families"""
        return len(self.control_families)
    
    def validate_control_ids(self) -> Dict[str, List[str]]:
        """Validate that all control IDs are unique across the framework"""
        control_ids = []
        duplicates = []
        
        for control in self.get_all_controls():
            if control.control_id in control_ids:
                duplicates.append(control.control_id)
            else:
                control_ids.append(control.control_id)
        
        return {
            "valid": len(duplicates) == 0,
            "duplicate_control_ids": duplicates,
            "total_unique_controls": len(control_ids)
        }
    
    def get_framework_info(self) -> Dict[str, Any]:
        """Get comprehensive framework information"""
        validation = self.validate_control_ids()
        
        return {
            "framework_id": self.framework_id,
            "framework_name": self.framework_name,
            "total_controls": self.get_control_count(),
            "total_families": self.get_family_count(),
            "validation": validation,
            "families": [
                {
                    "family_id": family.family_id,
                    "family_name": family.family_name,
                    "control_count": len(family.get_controls())
                }
                for family in self.control_families
            ]
        } 