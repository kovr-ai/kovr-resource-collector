"""
Resources module for provider-specific resource models.
"""
import yaml
import os
from typing import Dict, Any, List, Type
from pydantic import BaseModel
from .models import Resource, ResourceCollection
from .dynamic_models import initialize_dynamic_models, get_dynamic_models

# Global storage for loaded resource definitions (legacy)
_loaded_resources: Dict[str, Dict[str, Any]] = {}

# Global storage for dynamic Pydantic models
_dynamic_models: Dict[str, Type[BaseModel]] = {}

def load_resources_from_yaml(yaml_file_path: str = None):
    """
    Load resource definitions from YAML file and create dynamic Pydantic models.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to resources/resources.yaml
    """
    global _loaded_resources, _dynamic_models
    
    if yaml_file_path is None:
        # Default to resources.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'resources.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        # Store resource definitions (legacy)
        if 'resources' in yaml_data:
            _loaded_resources = yaml_data['resources']
        
        # Create dynamic Pydantic models
        from .dynamic_models import load_and_create_dynamic_models
        _dynamic_models = load_and_create_dynamic_models(yaml_file_path)
        
        # Make dynamic models accessible as module attributes
        for model_name, model_class in _dynamic_models.items():
            globals()[model_name] = model_class
        
        print(f"✅ Loaded {len(_loaded_resources)} resource definitions and created {len(_dynamic_models)} Pydantic models from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ Resources YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading resources from YAML: {e}")

def get_loaded_resources() -> Dict[str, Dict[str, Any]]:
    """Get all loaded resource definitions (legacy)."""
    return _loaded_resources.copy()

def get_dynamic_resource_models() -> Dict[str, Type[BaseModel]]:
    """Get all dynamic Pydantic resource models."""
    return _dynamic_models.copy()

def get_resource_model(name: str) -> Type[BaseModel]:
    """Get a specific dynamic resource model by name."""
    return _dynamic_models.get(name)

# Auto-load resources when module is imported
load_resources_from_yaml() 