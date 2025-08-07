"""
Utils package for con_mon - contains helper functions and SQL operations.
"""
import os
import yaml
import importlib
from pydantic import BaseModel, Field
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


def format_class_name(name: str) -> str:
    """
    Format a name into a proper class name prefix.
    
    Args:
        name: Raw name from YAML (e.g., 'github', 'aws', 'gcp')
        
    Returns:
        Formatted class name prefix (e.g., 'Github', 'Aws', 'GCP')
    """
    return name.title()


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
        name = connector_data.get('name')
        
        if not provider_service:
            raise ValueError("provider_service is required in connector configuration")
        if not name:
            raise ValueError("name is required in connector configuration")
            
        fetch_function = create_fetch_function(provider_service, method_name)
        
        # Create a subclass of ConnectorService with proper field definitions
        class_name = f"{format_class_name(name)}ConnectorService"
        
        # Create the class dynamically
        service_class = type(
            class_name,
            (ConnectorService,),
            {
                '__annotations__': {
                    'name': str,
                    'description': str,
                    'connector_type': ConnectorType,
                    'fetch_function': Callable[[ConnectorInput], ResourceCollection]
                },
                'name': Field(default=name),
                'description': Field(default=connector_data.get('description', f"{name} connector")),
                'connector_type': Field(default=ConnectorType(connector_data.get('connector_type'))),
                'fetch_function': Field(default=fetch_function)
            }
        )
        
        return service_class

    @staticmethod
    def _create_connector_input_class(input_data: dict[str, Any], connector_name: str) -> Type[ConnectorInput]:
        """Create a ConnectorInput subclass from input data."""
        class_name = f"{format_class_name(connector_name)}ConnectorInput"
        
        # Create field definitions with proper type annotations
        annotations = {}
        fields = {}
        for field_name, field_type in input_data.items():
            if field_name != 'name':  # Skip the name field
                if field_type == "string":
                    annotations[field_name] = str
                    fields[field_name] = Field(...)  # Required field
                # Add more type mappings as needed
        
        # Create the class dynamically
        input_class = type(
            class_name,
            (ConnectorInput,),
            {
                '__annotations__': annotations,
                **fields
            }
        )
        
        return input_class

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
            connector_data = provider_data.get('connector', {})
            connector_class = cls._create_connector_service_class(connector_data)
            input_class = cls._create_connector_input_class(
                {k: v for k, v in provider_data.get('input', {}).items() if k != 'name'},  # Exclude name from fields
                provider_data.get('input', {}).get('name', connector_data.get('name', provider_name))  # Use input name or fallback
            )
        except Exception as e:
            raise ValueError(f"Error processing connector '{provider_name}': {str(e)}")

        return cls(
            connector=connector_class,
            input=input_class
        )


class ResourceYamlMapping(BaseModel):
    """Mapping class for resource configurations from YAML."""
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
        # Use the key directly as class name
        class_name = schema_name
        
        # Create field definitions with proper type annotations
        annotations = {}
        fields = {}
        for field_name, field_type in schema_def.get('fields', {}).items():
            # Handle nested field types
            if isinstance(field_type, dict):
                if field_type.get('type') == 'array':
                    annotations[field_name] = list
                elif field_type.get('type') == 'object':
                    annotations[field_name] = dict
                else:
                    annotations[field_name] = str
            else:
                # Map YAML types to Python types
                type_mapping = {
                    'string': str,
                    'integer': int,
                    'boolean': bool,
                    'array': list,
                    'object': dict,
                    'number': float
                }
                annotations[field_name] = type_mapping.get(field_type, str)
            
            fields[field_name] = Field(default=None)
        
        return type(
            class_name,
            (ResourceField,),
            {
                '__annotations__': annotations,
                **fields
            }
        )

    @staticmethod
    def _create_resource_class(resource_def: dict[str, Any], resource_name: str) -> Type[Resource]:
        """Create a Resource subclass from resource definition."""
        # Use the key directly as class name
        class_name = resource_name
        
        # Create field definitions with proper type annotations
        annotations = {
            'service': str  # Add type annotation for service field
        }
        fields = {
            'service': Field(default=resource_def.get('service'))  # Add service field for AWS resources
        }
        
        for field_name, field_type in resource_def.get('fields', {}).items():
            # Handle nested field types and references
            if isinstance(field_type, str):
                # If it's a reference to another schema
                if field_type in ['RepositoryData', 'ActionsData', 'SecurityData', 'OrganizationData', 'AdvancedFeaturesData']:
                    annotations[field_name] = Any  # We'll resolve these later
                else:
                    # Map YAML types to Python types
                    type_mapping = {
                        'string': str,
                        'integer': int,
                        'boolean': bool,
                        'array': list,
                        'object': dict,
                        'number': float
                    }
                    annotations[field_name] = type_mapping.get(field_type, str)
            elif isinstance(field_type, dict):
                if field_type.get('type') == 'array':
                    annotations[field_name] = list
                elif field_type.get('type') == 'object':
                    annotations[field_name] = dict
                else:
                    annotations[field_name] = str
            
            fields[field_name] = Field(default=None)
        
        return type(
            class_name,
            (Resource,),
            {
                '__annotations__': annotations,
                **fields
            }
        )

    @staticmethod
    def _create_resource_collection_class(collection_def: dict[str, Any], provider_name: str) -> Type[ResourceCollection]:
        """Create a ResourceCollection subclass from collection definition."""
        # Use the name field to generate the class name
        class_name = f"{format_class_name(provider_name)}ResourceCollection"
        
        # Create field definitions with proper type annotations
        annotations = {}
        fields = {}
        for field_name, field_type in collection_def.get('fields', {}).items():
            if isinstance(field_type, list):
                annotations[field_name] = list  # For resource references
            elif isinstance(field_type, dict):
                annotations[field_name] = dict  # For metadata
            else:
                annotations[field_name] = str
            
            fields[field_name] = Field(default=None)
        
        return type(
            class_name,
            (ResourceCollection,),
            {
                '__annotations__': annotations,
                **fields
            }
        )

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

            # Extract nested schemas - use key directly as class name
            for schema_name, schema_def in provider_config.get('nested_schemas', {}).items():
                schema_class = cls._create_resource_field_class(schema_def, schema_name)
                all_nested_schemas.append(schema_class)

            # Extract resources - use key directly as class name
            for resource_name, resource_def in provider_config.get('resources', {}).items():
                resource_class = cls._create_resource_class(resource_def, resource_name)
                all_resources.append(resource_class)

            # Extract resource collection - use name field for class name
            collection_data = provider_config.get('resource_collection')
            if collection_data:
                collection_class = cls._create_resource_collection_class(
                    collection_data,
                    collection_data.get('name', provider_name)
                )

        if not collection_class:
            collection_class = ResourceCollection  # Use base class if no custom collection defined

        return cls(
            nested_schemas=all_nested_schemas,
            resources=all_resources,
            resources_collection=collection_class
        )
