from typing import Dict, List, Optional, Type
from .base_framework import BaseFramework
from .nist_800_53 import NIST80053Framework
from .iso_27001.iso_framework import ISO27001Framework

class FrameworkRegistry:
    """Registry for managing multiple compliance frameworks"""
    
    def __init__(self):
        self._frameworks: Dict[str, BaseFramework] = {}
        self._framework_classes: Dict[str, Type[BaseFramework]] = {}
        self._initialize_default_frameworks()
    
    def _initialize_default_frameworks(self):
        """Initialize default frameworks"""
        # Register NIST 800-53
        self.register_framework("nist_800_53", NIST80053Framework())
        
        # Register ISO 27001 (example)
        self.register_framework("iso_27001", ISO27001Framework())
    
    def register_framework(self, framework_id: str, framework: BaseFramework):
        """Register a framework instance"""
        self._frameworks[framework_id] = framework
    
    def register_framework_class(self, framework_id: str, framework_class: Type[BaseFramework]):
        """Register a framework class for lazy instantiation"""
        self._framework_classes[framework_id] = framework_class
    
    def get_framework(self, framework_id: str) -> Optional[BaseFramework]:
        """Get a framework by ID"""
        # Check if framework is already instantiated
        if framework_id in self._frameworks:
            return self._frameworks[framework_id]
        
        # Check if framework class is registered and instantiate it
        if framework_id in self._framework_classes:
            framework = self._framework_classes[framework_id]()
            self._frameworks[framework_id] = framework
            return framework
        
        return None
    
    def get_all_frameworks(self) -> List[BaseFramework]:
        """Get all registered frameworks"""
        return list(self._frameworks.values())
    
    def get_framework_ids(self) -> List[str]:
        """Get all registered framework IDs"""
        return list(self._frameworks.keys())
    
    def get_framework_summary(self) -> Dict[str, Dict]:
        """Get summary of all frameworks"""
        summary = {}
        for framework_id, framework in self._frameworks.items():
            summary[framework_id] = {
                "framework_name": framework.framework_name,
                "total_controls": framework.get_control_count(),
                "total_families": framework.get_family_count(),
                "validation": framework.validate_control_ids()
            }
        return summary
    
    def get_framework_info(self, framework_id: str) -> Optional[Dict]:
        """Get detailed information about a specific framework"""
        framework = self.get_framework(framework_id)
        if framework:
            return framework.get_framework_info()
        return None
    
    def validate_all_frameworks(self) -> Dict[str, Dict]:
        """Validate all frameworks"""
        validation_results = {}
        for framework_id, framework in self._frameworks.items():
            validation_results[framework_id] = {
                "framework_name": framework.framework_name,
                "validation": framework.validate_control_ids()
            }
        return validation_results
    
    def get_control_by_id(self, framework_id: str, control_id: str):
        """Get a specific control from a specific framework"""
        framework = self.get_framework(framework_id)
        if framework:
            return framework.get_control_by_id(control_id)
        return None
    
    def get_family_by_id(self, framework_id: str, family_id: str):
        """Get a specific family from a specific framework"""
        framework = self.get_framework(framework_id)
        if framework:
            return framework.get_family_by_id(family_id)
        return None
    
    def list_available_frameworks(self) -> List[Dict]:
        """List all available frameworks with basic info"""
        frameworks = []
        for framework_id, framework in self._frameworks.items():
            frameworks.append({
                "framework_id": framework_id,
                "framework_name": framework.framework_name,
                "total_controls": framework.get_control_count(),
                "total_families": framework.get_family_count()
            })
        return frameworks
    
    def remove_framework(self, framework_id: str) -> bool:
        """Remove a framework from the registry"""
        if framework_id in self._frameworks:
            del self._frameworks[framework_id]
            return True
        return False
    
    def clear_frameworks(self):
        """Clear all frameworks from the registry"""
        self._frameworks.clear()
        self._framework_classes.clear()
        self._initialize_default_frameworks()

# Global registry instance
framework_registry = FrameworkRegistry() 