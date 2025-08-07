"""
con_mon_v2 package - Resource collector for KOVR.

This package provides a dynamic class mapping system that allows importing
dynamically created classes as if they were statically defined.

Example:
    # Connector classes
    from con_mon_v2.mappings.github import GithubConnectorService
    from con_mon_v2.mappings.github import GithubConnectorInput
    from con_mon_v2.mappings.aws import AwsConnectorService
    from con_mon_v2.mappings.aws import AwsConnectorInput

    # Resource classes
    from con_mon_v2.mappings.github import GithubResource
    from con_mon_v2.mappings.github import GithubResourceCollection
    from con_mon_v2.mappings.aws import EC2Resource
    from con_mon_v2.mappings.aws import AwsResourceCollection
"""
import os
import sys
import yaml
import types
from pathlib import Path
from con_mon_v2.utils.yaml_loader import ConnectorYamlMapping, ResourceYamlMapping

# Global storage for dynamically created classes
mappings = {}

def _create_module(name: str) -> types.ModuleType:
    """Create a new module and register it in sys.modules."""
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module

# Create the base mappings package
_create_module('con_mon_v2.mappings')

def _load_connector_mappings():
    """Load all connector mappings from YAML files."""
    # Get the connectors directory
    connectors_dir = Path(__file__).parent / 'connectors'
    yaml_path = connectors_dir / 'connectors.yaml'

    if not yaml_path.exists():
        print(f"Warning: No connectors.yaml found at {yaml_path}")
        return

    try:
        with open(yaml_path, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Process each provider's configuration
        for provider_name, provider_data in yaml_data.items():
            # Create connector mapping
            connector_mapping = ConnectorYamlMapping.load_yaml({provider_name: provider_data})
            
            # Store classes in the global mappings
            if provider_name not in mappings:
                mappings[provider_name] = {}
            
            # Store connector service class
            service_class = connector_mapping.connector
            mappings[provider_name][service_class.__name__] = service_class
            
            # Store input class
            input_class = connector_mapping.input
            mappings[provider_name][input_class.__name__] = input_class

            # Create and register the provider-specific module
            module_name = f"con_mon_v2.mappings.{provider_name}"
            if module_name not in sys.modules:
                provider_module = _create_module(module_name)
            else:
                provider_module = sys.modules[module_name]
            
            # Add classes to the module
            setattr(provider_module, service_class.__name__, service_class)
            setattr(provider_module, input_class.__name__, input_class)

            # Update module's __all__ attribute
            if not hasattr(provider_module, '__all__'):
                provider_module.__all__ = []
            provider_module.__all__.extend([service_class.__name__, input_class.__name__])

    except Exception as e:
        print(f"Error loading connector mappings: {str(e)}")

def _load_resource_mappings():
    """Load all resource mappings from YAML files."""
    # Get the resources directory
    resources_dir = Path(__file__).parent / 'resources'
    yaml_path = resources_dir / 'resources.yaml'

    if not yaml_path.exists():
        print(f"Warning: No resources.yaml found at {yaml_path}")
        return

    try:
        with open(yaml_path, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Process each provider's configuration
        for provider_name, provider_data in yaml_data.items():
            # Create resource mapping
            resource_mapping = ResourceYamlMapping.load_yaml({provider_name: provider_data})
            
            # Store classes in the global mappings
            if provider_name not in mappings:
                mappings[provider_name] = {}
            
            # Store resource classes
            for resource_class in resource_mapping.resources:
                mappings[provider_name][resource_class.__name__] = resource_class
            
            # Store nested schema classes
            for schema_class in resource_mapping.nested_schemas:
                mappings[provider_name][schema_class.__name__] = schema_class
            
            # Store resource collection class
            collection_class = resource_mapping.resources_collection
            mappings[provider_name][collection_class.__name__] = collection_class

            # Create and register the provider-specific module
            module_name = f"con_mon_v2.mappings.{provider_name}"
            if module_name not in sys.modules:
                provider_module = _create_module(module_name)
            else:
                provider_module = sys.modules[module_name]
            
            # Add classes to the module
            for resource_class in resource_mapping.resources:
                setattr(provider_module, resource_class.__name__, resource_class)
            for schema_class in resource_mapping.nested_schemas:
                setattr(provider_module, schema_class.__name__, schema_class)
            setattr(provider_module, collection_class.__name__, collection_class)

            # Update module's __all__ attribute
            if not hasattr(provider_module, '__all__'):
                provider_module.__all__ = []
            provider_module.__all__.extend([
                *[rc.__name__ for rc in resource_mapping.resources],
                *[sc.__name__ for sc in resource_mapping.nested_schemas],
                collection_class.__name__
            ])

    except Exception as e:
        print(f"Error loading resource mappings: {str(e)}")


# Load mappings when the package is imported
_load_connector_mappings()
_load_resource_mappings()

# Export the mappings
__all__ = ['mappings']