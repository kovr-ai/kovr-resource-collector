"""
Resources module for provider-specific resource models.
"""
import yaml
import os
from typing import Dict, Any, List
from .models import Resource

# Global storage for loaded resource definitions
_loaded_resources: Dict[str, Dict[str, Any]] = {}

def load_resources_from_yaml(yaml_file_path: str = None):
    """
    Load resource definitions from YAML file.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to resources/resources.yaml
    """
    global _loaded_resources
    
    if yaml_file_path is None:
        # Default to resources.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'resources.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        # Store resource definitions
        if 'resources' in yaml_data:
            _loaded_resources = yaml_data['resources']
            
            # Make resources accessible as module attributes
            for resource_name, resource_config in _loaded_resources.items():
                globals()[resource_name] = resource_config
        
        print(f"✅ Loaded {len(_loaded_resources)} resource definitions from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ Resources YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading resources from YAML: {e}")

def get_loaded_resources() -> Dict[str, Dict[str, Any]]:
    """Get all loaded resource definitions."""
    return _loaded_resources.copy()

# Auto-load resources when module is imported
load_resources_from_yaml() 