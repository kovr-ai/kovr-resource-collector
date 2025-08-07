"""
Utils package for con_mon - contains helper functions and SQL operations.
"""
import os
import yaml
import importlib
from pydantic import BaseModel
from typing import Any, Callable, Type
from con_mon_v2.connectors import ConnectorService, ConnectorInput, ConnectorType
from con_mon_v2.resources import Resource, ResourceCollection, ResourceField


def create_fetch_function(provider_module_path: str, method_name: str) -> Callable[[ConnectorInput], ResourceCollection]:
    """
    Create a fetch function by importing the provider module and finding the provider class.

    Args:
        provider_module_path: Python path to the provider module
        method_name: Name of the method to call on the provider instance

    Returns:
        A callable that takes ConnectorInput and returns ResourceCollection

    Raises:
        ImportError: If the provider module cannot be imported
        ValueError: If the provider class or method is not found
    """
    module = importlib.import_module(provider_module_path)
    
    # Look for provider class
    provider_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            hasattr(attr, '_is_provider') and 
            attr._is_provider):
            provider_class = attr
            break
    
    if not provider_class or not hasattr(provider_class, method_name):
        raise ValueError(f"Provider class or method '{method_name}' not found in {provider_module_path}")

    def fetch_function(input_config: ConnectorInput) -> ResourceCollection:
        # Convert input_config to dictionary for metadata
        if hasattr(input_config, 'dict'):
            metadata = input_config.dict()
        elif hasattr(input_config, 'model_dump'):
            metadata = input_config.model_dump()
        else:
            metadata = dict(input_config)
        
        provider_instance = provider_class(metadata)
        return getattr(provider_instance, method_name)()

    return fetch_function


class ConnectorYamlMapping(BaseModel):
    """Mapping class for connector configurations from YAML."""
    connector: Type[ConnectorService]
    input: Type[ConnectorInput]

    @staticmethod
    def _load_yaml_data(path_or_dict: str | dict) -> dict:
        """
        Load YAML data from either a file path or a dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            dict: The loaded YAML data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        if isinstance(path_or_dict, str):
            if not os.path.exists(path_or_dict):
                raise FileNotFoundError(f"YAML file not found: {path_or_dict}")
            
            with open(path_or_dict, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(path_or_dict, dict):
            return path_or_dict
        else:
            raise ValueError("Input must be either a file path (str) or a dictionary")

    @staticmethod
    def _create_connector_service_class(connector_data: dict[str, Any]) -> Type[ConnectorService]:
        """Create a ConnectorService subclass from connector data."""
        provider_service = connector_data.get('provider_service')
        method_name = connector_data.get('method', 'process')
        
        if not provider_service:
            raise ValueError("provider_service is required in connector configuration")
            
        fetch_function = create_fetch_function(provider_service, method_name)
        
        # Create a subclass of ConnectorService with the configured values
        class_name = f"{connector_data.get('name', 'Unknown').title()}ConnectorService"
        return type(class_name, (ConnectorService,), {
            'name': connector_data.get('name'),
            'description': connector_data.get('description', f"{connector_data.get('name')} connector"),
            'connector_type': ConnectorType(connector_data.get('connector_type')),
            'fetch_function': fetch_function
        })

    @staticmethod
    def _create_connector_input_class(input_data: dict[str, Any], connector_name: str) -> Type[ConnectorInput]:
        """Create a ConnectorInput subclass from input data."""
        class_name = f"{connector_name.title()}ConnectorInput"
        fields = {}
        for field_name, field_type in input_data.items():
            if field_type == "string":
                fields[field_name] = (str, ...)  # Required string field
            # Add more type mappings as needed
        
        return type(class_name, (ConnectorInput,), {
            '__annotations__': {k: v[0] for k, v in fields.items()},
            **{k: v[1] for k, v in fields.items()}
        })

    @classmethod
    def load_yaml(cls, path_or_dict: str | dict) -> 'ConnectorYamlMapping':
        """
        Load connector configuration from a YAML file or dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            ConnectorYamlMapping: An instance of ConnectorYamlMapping containing the loaded data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        yaml_data = cls._load_yaml_data(path_or_dict)

        # We expect only one provider configuration in the YAML
        if not yaml_data or not isinstance(yaml_data, dict):
            raise ValueError("Invalid YAML data: expected a dictionary with provider configuration")

        # Get the first provider's data
        provider_name = next(iter(yaml_data))
        provider_data = yaml_data[provider_name]

        try:
            connector_class = cls._create_connector_service_class(provider_data.get('connector', {}))
            input_class = cls._create_connector_input_class(
                provider_data.get('input', {}),
                provider_data.get('connector', {}).get('name', provider_name)
            )
        except Exception as e:
            raise ValueError(f"Error processing connector '{provider_name}': {str(e)}")

        return cls(
            connector=connector_class,
            input=input_class
        )


class ResourceYamlMapping(BaseModel):
    nested_schemas: list[Type[ResourceField]]
    resources: list[Type[Resource]]
    resources_collection: Type[ResourceCollection]

    @staticmethod
    def _load_yaml_data(path_or_dict: str | dict) -> dict:
        """
        Load YAML data from either a file path or a dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            dict: The loaded YAML data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        if isinstance(path_or_dict, str):
            if not os.path.exists(path_or_dict):
                raise FileNotFoundError(f"YAML file not found: {path_or_dict}")
            
            with open(path_or_dict, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(path_or_dict, dict):
            return path_or_dict
        else:
            raise ValueError("Input must be either a file path (str) or a dictionary")

    @staticmethod
    def _create_resource_field_class(schema_def: dict[str, Any], schema_name: str) -> Type[ResourceField]:
        """Create a ResourceField subclass from schema definition."""
        class_name = f"{schema_name}ResourceField"
        return type(class_name, (ResourceField,), schema_def)

    @staticmethod
    def _create_resource_class(resource_def: dict[str, Any], resource_name: str) -> Type[Resource]:
        """Create a Resource subclass from resource definition."""
        class_name = f"{resource_name}Resource"
        return type(class_name, (Resource,), resource_def)

    @staticmethod
    def _create_resource_collection_class(collection_def: dict[str, Any]) -> Type[ResourceCollection]:
        """Create a ResourceCollection subclass from collection definition."""
        return type("CustomResourceCollection", (ResourceCollection,), collection_def)

    @classmethod
    def load_yaml(cls, path_or_dict: str | dict) -> 'ResourceYamlMapping':
        """
        Load resource configuration from a YAML file or dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            ResourceYamlMapping: An instance of ResourceYamlMapping containing the loaded data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        yaml_data = cls._load_yaml_data(path_or_dict)
        
        all_nested_schemas = []
        all_resources = []
        collection_class = None

        # Process each provider's configuration
        for provider_name, provider_config in yaml_data.items():
            if not isinstance(provider_config, dict):
                continue

            # Extract nested schemas
            field_schemas = provider_config.get('resources_field_schemas', {})
            for schema_name, schema_def in field_schemas.items():
                schema_class = cls._create_resource_field_class(schema_def, schema_name)
                all_nested_schemas.append(schema_class)

            # Extract resources
            resources_data = provider_config.get('resources', {})
            for resource_name, resource_def in resources_data.items():
                resource_class = cls._create_resource_class(resource_def, resource_name)
                all_resources.append(resource_class)

            # Extract resource collection
            collection_data = provider_config.get('ResourceCollection')
            if collection_data:
                collection_class = cls._create_resource_collection_class(collection_data)

        if not collection_class:
            collection_class = ResourceCollection  # Use base class if no custom collection defined

        return cls(
            nested_schemas=all_nested_schemas,
            resources=all_resources,
            resources_collection=collection_class
        )
