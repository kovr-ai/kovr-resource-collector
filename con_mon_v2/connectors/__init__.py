"""
Connectors module for data fetching service definitions.

Simple connector loading from YAML configuration.

Usage:
    from connectors import github, GithubConnectorInput
    input_config = GithubConnectorInput(GITHUB_TOKEN="your_token")
    result = github.fetch_data(input_config)
"""
import yaml
import os
import importlib
from typing import Dict, Any
from pydantic import BaseModel
from .models import ConnectorService, ConnectorType, ConnectorInput

# Global storage for loaded connectors
_loaded_connectors: Dict[str, Any] = {}


def create_input_class_from_yaml(input_spec: Dict[str, str], class_name: str):
    """
    Dynamically create a Pydantic input class from YAML input specification.

    Args:
        input_spec: Dictionary of field_name -> field_type from YAML
        class_name: Name for the generated class

    Returns:
        Dynamically created Pydantic model class
    """
    fields = {}
    for field_name, field_type in input_spec.items():
        if field_type == "string":
            fields[field_name] = (str, ...)  # Required string field
        # Add more type mappings as needed

    return type(class_name, (BaseModel,), {
        '__annotations__': {k: v[0] for k, v in fields.items()},
        **{k: v[1] for k, v in fields.items()}
    })


def load_connectors_from_yaml(yaml_file_path: str = None):
    """
    Load connector configurations from YAML file and create connector services.

    Args:
        yaml_file_path: Path to YAML file, defaults to connectors/connectors.yaml
    """
    global _loaded_connectors

    if yaml_file_path is None:
        # Default to connectors.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'connectors.yaml')

    loaded_connector_names = []
    loaded_input_classes = []

    with open(yaml_file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)

    # Process connectors - handle new structure where each connector is a top-level key
    for connector_name, connector_data in yaml_data.items():
        connector_config = connector_data['connectors']
        _loaded_connectors[connector_name] = connector_config

        # Create input class from YAML input specification
        input_class_name = f"{connector_name.title()}ConnectorInput"
        input_class = create_input_class_from_yaml(
            connector_data['input'],
            input_class_name
        )
        globals()[input_class_name] = input_class
        loaded_input_classes.append(input_class_name)

        # Import provider module
        provider_service_path = connector_config['provider_service']
        method_name = connector_config['method']

        module = importlib.import_module(provider_service_path)

        # Look for provider class
        provider_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                    hasattr(attr, '_is_provider') and
                    attr._is_provider):
                provider_class = attr
                break

        # Create wrapper function
        def create_fetch_function(provider_cls, method):
            def fetch_function(input_config):
                # Convert input_config to dictionary for metadata
                if hasattr(input_config, 'dict'):
                    metadata = input_config.dict()
                elif hasattr(input_config, 'model_dump'):
                    metadata = input_config.model_dump()
                else:
                    metadata = dict(input_config)

                provider_instance = provider_cls(metadata)
                return getattr(provider_instance, method)()

            return fetch_function

        # Create connector service
        connector_service = ConnectorService(
            name=connector_config['name'],
            description=connector_config.get('description', f"{connector_config['name']} connector"),
            connector_type=ConnectorType(connector_config['connector_type']),
            fetch_function=create_fetch_function(provider_class, method_name)
        )

        # Make connector available as module attribute
        globals()[connector_name] = connector_service
        loaded_connector_names.append(connector_name)

    print(f"✅ Loaded {len(_loaded_connectors)} connectors from {yaml_file_path}")

    # Update __all__ dynamically
    globals()['__all__'] = [
                               'ConnectorService',
                               'ConnectorType',
                               'get_loaded_connectors',
                               'get_connector_by_id',
                               'get_connector_input_by_id'
                           ] + loaded_connector_names + loaded_input_classes

    print(f"📦 Available connectors: {loaded_connector_names}")
    print(f"📦 Available input classes: {loaded_input_classes}")


def get_loaded_connectors() -> Dict[str, Any]:
    """Get all loaded connector configurations."""
    return _loaded_connectors.copy()
