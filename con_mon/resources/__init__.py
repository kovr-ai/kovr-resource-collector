"""
Resources module for provider-specific resource models.
"""
import yaml
import os
from typing import Dict, Any, List, Type
from pydantic import BaseModel
from .models import Resource, ResourceCollection
from .dynamic_models import get_dynamic_models

# Global storage for loaded resource definitions (legacy)
_loaded_resources: Dict[str, Dict[str, Any]] = {}

def load_resources_from_yaml(yaml_file_path: str = None):
    """
    Load resource definitions from YAML file and create dynamic Pydantic models.
    
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
        
        # Count all resource definitions across providers
        total_resource_definitions = 0
        provider_info = []
        
        for provider_name, provider_config in yaml_data.items():
            if not isinstance(provider_config, dict):
                continue
                
            # Count resources from resources_field_schemas section
            field_schemas = provider_config.get('resources_field_schemas', {})
            field_schema_count = len(field_schemas)
            
            # Count resources from resources section
            resources = provider_config.get('resources', {})
            resource_count = len(resources)
            
            # Count collections
            collection_count = 1 if provider_config.get('ResourceCollection') else 0
            
            provider_total = field_schema_count + resource_count + collection_count
            total_resource_definitions += provider_total
            
            if provider_total > 0:
                provider_info.append(f"{provider_name}: {field_schema_count} field schemas + {resource_count} resources + {collection_count} collections")
        
        # Store resource definitions (legacy - for backwards compatibility)
        # This flattens all resources for legacy code
        _loaded_resources = {}
        for provider_name, provider_config in yaml_data.items():
            if isinstance(provider_config, dict):
                if 'resources' in provider_config:
                    _loaded_resources.update(provider_config['resources'])
        
        # Get dynamic models from the single source of truth
        dynamic_models = get_dynamic_models()
        
        # Make dynamic models accessible as module attributes
        for model_name, model_class in dynamic_models.items():
            globals()[model_name] = model_class
        
        print(f"✅ Loaded {total_resource_definitions} resource definitions and created {len(dynamic_models)} Pydantic models from {yaml_file_path}")
        if provider_info:
            print(f"   Provider breakdown: {', '.join(provider_info)}")
        
        # List the created models by provider
        github_models = [name for name in dynamic_models.keys() if 'Github' in name or name in ['RepositoryData', 'ActionsData', 'CollaborationData', 'SecurityData', 'OrganizationData', 'AdvancedFeaturesData']]
        aws_models = [name for name in dynamic_models.keys() if name.startswith('AWS')]
        
        if github_models:
            print(f"   GitHub models: {', '.join(sorted(github_models))}")
        if aws_models:
            print(f"   AWS models: {', '.join(sorted(aws_models))}")
        
    except FileNotFoundError:
        print(f"❌ Resources YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading resources from YAML: {e}")
        import traceback
        traceback.print_exc()

def get_loaded_resources() -> Dict[str, Dict[str, Any]]:
    """Get all loaded resource definitions (legacy)."""
    return _loaded_resources.copy()

def get_dynamic_resource_models() -> Dict[str, Type[BaseModel]]:
    """Get all dynamic Pydantic resource models."""
    return get_dynamic_models()

def get_resource_model(name: str) -> Type[BaseModel]:
    """Get a specific dynamic resource model by name."""
    dynamic_models = get_dynamic_models()
    return dynamic_models.get(name)

def list_available_models() -> Dict[str, List[str]]:
    """List all available models grouped by provider."""
    dynamic_models = get_dynamic_models()
    
    github_models = []
    aws_models = []
    other_models = []
    
    for model_name in dynamic_models.keys():
        if 'Github' in model_name or model_name in ['RepositoryData', 'ActionsData', 'CollaborationData', 'SecurityData', 'OrganizationData', 'AdvancedFeaturesData']:
            github_models.append(model_name)
        elif model_name.startswith('AWS'):
            aws_models.append(model_name)
        else:
            other_models.append(model_name)
    
    return {
        'github': sorted(github_models),
        'aws': sorted(aws_models),
        'other': sorted(other_models)
    }

# Auto-load resources when module is imported
load_resources_from_yaml() 