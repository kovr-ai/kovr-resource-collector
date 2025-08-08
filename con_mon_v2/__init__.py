"""
con_mon_v2 package - Resource collector for KOVR.

This package provides a dynamic class mapping system that allows importing
dynamically created classes as if they were statically defined.

All classes and instances are created dynamically from YAML configurations:
- Resource models from resources.yaml
- Connector services from connectors.yaml
"""
import os
import sys
import types
from pathlib import Path
from con_mon_v2.utils.yaml_loader import ConnectorYamlMapping, ResourceYamlMapping

def _create_module(name: str) -> types.ModuleType:
    """Create a new module and register it in sys.modules."""
    if name not in sys.modules:
        module = types.ModuleType(name)
        sys.modules[name] = module
        return module
    return sys.modules[name]

# Create base mappings package
_create_module('con_mon_v2.mappings')

def _load_mappings():
    """Load all mappings from YAML files."""
    try:
        # Load resource mappings
        resources_yaml = Path(__file__).parent / 'resources' / 'resources.yaml'
        if resources_yaml.exists():
            resource_mappings = ResourceYamlMapping.load_yaml(resources_yaml)
            for provider_name, mapping in resource_mappings.items():
                # Create provider module
                provider_module = _create_module(f'con_mon_v2.mappings.{provider_name}')
                
                # Add resource classes
                for resource in mapping.resources:
                    setattr(provider_module, resource.__name__, resource)
                
                # Add nested schema classes
                for schema in mapping.nested_schemas:
                    setattr(provider_module, schema.__name__, schema)
                
                # Add collection class
                setattr(provider_module, mapping.resources_collection.__name__, mapping.resources_collection)

        # Load connector mappings
        connectors_yaml = Path(__file__).parent / 'connectors' / 'connectors.yaml'
        if connectors_yaml.exists():
            connector_mappings = ConnectorYamlMapping.load_yaml(connectors_yaml)
            for provider_name, mapping in connector_mappings.items():
                # Get or create provider module
                provider_module = _create_module(f'con_mon_v2.mappings.{provider_name}')
                
                # Add connector service class and instance
                service_class = mapping.connector
                setattr(provider_module, service_class.__name__, service_class)
                
                # Add input class
                input_class = mapping.input
                setattr(provider_module, input_class.__name__, input_class)
                
                # Create service instance
                instance_name = f"{provider_name}_connector_service"
                instance = service_class()  # The class already has all needed fields from YAML
                setattr(provider_module, instance_name, instance)

    except Exception as e:
        print(f"Error loading mappings: {str(e)}")

# Load all mappings when package is imported
_load_mappings()