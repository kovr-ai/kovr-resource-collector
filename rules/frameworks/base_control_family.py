from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from rules.frameworks.base_control import BaseControl

class BaseControlFamily(ABC):
    """Base class for all control families"""
    
    def __init__(self, family_id: str, family_name: str):
        self.family_id = family_id
        self.family_name = family_name
        self.controls = []
    
    @abstractmethod
    def initialize_controls(self):
        """Initialize controls for this family - must be implemented by subclasses"""
        pass
    
    def get_controls(self) -> List[BaseControl]:
        """Return all controls in this family"""
        return self.controls
    
    def get_control_by_id(self, control_id: str) -> Optional[BaseControl]:
        """Get a specific control by ID"""
        for control in self.controls:
            if control.control_id == control_id:
                return control
        return None
    
    def add_control(self, control: BaseControl):
        """Add a control to this family"""
        existing_control = self.get_control_by_id(control.control_id)
        if existing_control:
            raise ValueError(f"Control with ID {control.control_id} already exists in family {self.family_id}")
        
        self.controls.append(control)
    
    def remove_control(self, control_id: str) -> bool:
        """Remove a control from this family by ID"""
        for i, control in enumerate(self.controls):
            if control.control_id == control_id:
                del self.controls[i]
                return True
        return False
    
    def get_control_count(self) -> int:
        """Get the number of controls in this family"""
        return len(self.controls)
    
    def get_family_summary(self) -> Dict[str, Any]:
        """Get summary of this control family"""
        return {
            "family_id": self.family_id,
            "family_name": self.family_name,
            "control_count": self.get_control_count(),
            "controls": [
                {
                    "control_id": control.control_id,
                    "control_name": control.control_name,
                    "check_count": len(control.checks)
                }
                for control in self.controls
            ]
        }
    
    def validate_control_ids(self) -> Dict[str, List[str]]:
        """Validate that all control IDs are unique within this family"""
        control_ids = []
        duplicates = []
        
        for control in self.controls:
            if control.control_id in control_ids:
                duplicates.append(control.control_id)
            else:
                control_ids.append(control.control_id)
        
        return {
            "valid": len(duplicates) == 0,
            "duplicate_control_ids": duplicates,
            "total_unique_controls": len(control_ids)
        }
    
    def get_controls_by_name_pattern(self, pattern: str) -> List[BaseControl]:
        """Get controls whose names match a pattern"""
        import re
        matching_controls = []
        
        for control in self.controls:
            if re.search(pattern, control.control_name, re.IGNORECASE):
                matching_controls.append(control)
        
        return matching_controls
    
    def sort_controls_by_id(self):
        """Sort controls by their control ID"""
        self.controls.sort(key=lambda x: x.control_id)
    
    def get_control_ids(self) -> List[str]:
        """Get list of all control IDs in this family"""
        return [control.control_id for control in self.controls]
    
    def get_control_names(self) -> List[str]:
        """Get list of all control names in this family"""
        return [control.control_name for control in self.controls] 