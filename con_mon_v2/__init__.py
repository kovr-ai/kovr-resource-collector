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

def _load_mappings():
    """Load all mappings from YAML files."""
    # Create base mappings package
    _create_module('con_mon_v2.mappings')

    # Load resource mappings first to ensure models are available
    resources_yaml = Path(__file__).parent / 'resources' / 'resources.yaml'
    if resources_yaml.exists():
        resource_mappings = ResourceYamlMapping.load_yaml(resources_yaml)
        for provider_name, mapping in resource_mappings.items():
            # Create provider module
            provider_module = _create_module(f'con_mon_v2.mappings.{provider_name}')

            # Add resource model classes
            for resource_mapping in mapping.resources:
                model_class = resource_mapping.pydantic_model
                setattr(provider_module, model_class.__name__, model_class)

            # Add collection model class
            collection_model = mapping.resources_collection.pydantic_model
            info_data_model = mapping.info_data.pydantic_model
            setattr(provider_module, collection_model.__name__, collection_model)
            setattr(provider_module, info_data_model.__name__, info_data_model)

    # from pdb import set_trace;set_trace()
    # Load connector mappings after resources are loaded
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

# Load all mappings when package is imported
_load_mappings()
