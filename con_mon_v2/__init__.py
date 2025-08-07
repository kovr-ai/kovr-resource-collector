"""
con_mon_v2 package - Resource collector for KOVR.

This package provides a dynamic class mapping system that allows importing
dynamically created classes as if they were statically defined.

Example:
    from con_mon_v2.mappings.github import GithubConnectorService
    from con_mon_v2.mappings.github import GithubConnectorInput
    from con_mon_v2.mappings.aws import AWSConnectorService
    from con_mon_v2.mappings.aws import AWSConnectorInput
"""
import os
import sys
import yaml
import types
from pathlib import Path
from con_mon_v2.utils.yaml_loader import ConnectorYamlMapping

# Global storage for dynamically created classes
mappings = {}

def _create_module(name: str) -> types.ModuleType:
    """Create a new module and register it in sys.modules."""
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module

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

        # Create the mappings package if it doesn't exist
        if 'con_mon_v2.mappings' not in sys.modules:
            _create_module('con_mon_v2.mappings')

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
            provider_module = _create_module(module_name)
            
            # Add classes to the module
            setattr(provider_module, service_class.__name__, service_class)
            setattr(provider_module, input_class.__name__, input_class)

            # Update module's __all__ attribute
            provider_module.__all__ = [service_class.__name__, input_class.__name__]

    except Exception as e:
        print(f"Error loading connector mappings: {str(e)}")

# Load mappings when the package is imported
_load_connector_mappings()

# Export the mappings
__all__ = ['mappings']