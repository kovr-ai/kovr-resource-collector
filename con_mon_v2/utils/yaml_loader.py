"""
Utils package for con_mon - contains helper functions and SQL operations.
"""
import os
import yaml
import importlib
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from con_mon_v2.connectors import ConnectorService, ConnectorInput, ConnectorType
from con_mon_v2.resources import Resource, ResourceCollection, ResourceField
from pathlib import Path


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
    def _load_yaml_data(path_or_dict: str | Path | dict) -> dict:
        """
        Load YAML data from either a file path or a dictionary.

        Args:
            path_or_dict: Either a path to a YAML file (str or Path) or a dictionary containing the YAML data

        Returns:
            dict: The loaded YAML data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        if isinstance(path_or_dict, (str, Path)):
            if not os.path.exists(str(path_or_dict)):
                raise FileNotFoundError(f"YAML file not found: {path_or_dict}")
            
            with open(path_or_dict, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(path_or_dict, dict):
            return path_or_dict
        else:
            raise ValueError("Input must be either a file path (str or Path) or a dictionary")

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
    def load_yaml(cls, path_or_dict: str | dict) -> Dict[str, 'ConnectorYamlMapping']:
        """
        Load connector configuration from a YAML file or dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            Dict[str, ConnectorYamlMapping]: A dictionary mapping provider names to their connector mappings

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        yaml_data = cls._load_yaml_data(path_or_dict)

        if not yaml_data or not isinstance(yaml_data, dict):
            raise ValueError("Invalid YAML data: expected a dictionary with provider configuration")

        result = {}
        for provider_name, provider_data in yaml_data.items():
            try:
                connector_data = provider_data.get('connector', {})
                connector_class = cls._create_connector_service_class(connector_data)
                input_class = cls._create_connector_input_class(
                    {k: v for k, v in provider_data.get('input', {}).items() if k != 'name'},  # Exclude name from fields
                    provider_data.get('input', {}).get('name', connector_data.get('name', provider_name))  # Use input name or fallback
                )
                result[provider_name] = cls(
                    connector=connector_class,
                    input=input_class
                )
            except Exception as e:
                raise ValueError(f"Error processing connector '{provider_name}': {str(e)}")

        return result


def yaml_type_to_python_type(yaml_type: str, available_models: Dict[str, Type[BaseModel]] = None) -> type:
    """Convert YAML type string to Python type, handling model references."""
    # Check if this is a reference to another model
    if available_models and yaml_type in available_models:
        return available_models[yaml_type]
    
    type_mapping = {
        'string': str,
        'integer': int,
        'boolean': bool,
        'float': float,
        'array': list,
        'object': dict,
        'datetime': datetime,
        'number': float
    }
    return type_mapping.get(yaml_type, str)


class ResourceYamlMapping(BaseModel):
    """Mapping class for resource configurations from YAML."""
    nested_schemas: list[Type[ResourceField]]
    resources: list[Type[Resource]]
    resources_collection: Type[ResourceCollection]

    @staticmethod
    def _load_yaml_data(path_or_dict: str | Path | dict) -> dict:
        """
        Load YAML data from either a file path or a dictionary.

        Args:
            path_or_dict: Either a path to a YAML file (str or Path) or a dictionary containing the YAML data

        Returns:
            dict: The loaded YAML data

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        if isinstance(path_or_dict, (str, Path)):
            if not os.path.exists(str(path_or_dict)):
                raise FileNotFoundError(f"YAML file not found: {path_or_dict}")
            
            with open(path_or_dict, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(path_or_dict, dict):
            return path_or_dict
        else:
            raise ValueError("Input must be either a file path (str or Path) or a dictionary")

    @staticmethod
    def _create_nested_model(name: str, fields_definition: Dict[str, Any], available_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
        """Create a nested Pydantic model from fields definition."""
        annotations = {}
        fields = {}
        
        for field_name, field_def in fields_definition.items():
            if isinstance(field_def, dict):
                # Handle nested field types
                if 'type' in field_def:
                    if field_def['type'] == 'array':
                        # Array with structure
                        if 'structure' in field_def:
                            item_model = ResourceYamlMapping._create_nested_model(
                                f"{name}_{field_name.title()}Item",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = List[item_model]
                            fields[field_name] = Field(default_factory=list)
                        else:
                            annotations[field_name] = List[str]
                            fields[field_name] = Field(default_factory=list)
                    elif field_def['type'] == 'object':
                        # Object with structure
                        if 'structure' in field_def:
                            nested_model = ResourceYamlMapping._create_nested_model(
                                f"{name}_{field_name.title()}",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = nested_model
                            fields[field_name] = Field(default_factory=lambda: nested_model())
                        else:
                            annotations[field_name] = Dict[str, Any]
                            fields[field_name] = Field(default_factory=dict)
                else:
                    # Legacy nested object format
                    nested_model = ResourceYamlMapping._create_nested_model(
                        f"{name}_{field_name.title()}",
                        field_def,
                        available_models
                    )
                    annotations[field_name] = nested_model
                    fields[field_name] = Field(default_factory=lambda: nested_model())
            elif field_def == 'array':
                # Simple array type
                annotations[field_name] = List[str]
                fields[field_name] = Field(default_factory=list)
            elif field_def in available_models:
                # Model reference
                annotations[field_name] = available_models[field_def]
                fields[field_name] = Field(default_factory=lambda: available_models[field_def]())
            else:
                # Simple field type
                field_type = yaml_type_to_python_type(str(field_def), available_models)
                annotations[field_name] = field_type
                fields[field_name] = Field(...)  # Required field
        
        return type(
            name,
            (BaseModel,),
            {
                '__annotations__': annotations,
                **fields
            }
        )

    @staticmethod
    def _create_resource_field_class(schema_def: dict[str, Any], schema_name: str, available_models: Dict[str, Type[BaseModel]] = None) -> Type[ResourceField]:
        """Create a ResourceField subclass from schema definition."""
        # Use the key directly as class name
        class_name = schema_name
        
        # Create field definitions with proper type annotations
        annotations = {}
        fields = {}
        
        # Add standard ResourceField fields
        annotations['name'] = str
        annotations['description'] = Optional[str]
        fields['name'] = Field(default=schema_def.get('name'))
        fields['description'] = Field(default=schema_def.get('description'))
        
        # Process schema fields
        schema_fields = schema_def.get('fields', {})
        for field_name, field_def in schema_fields.items():
            if isinstance(field_def, dict):
                # Handle nested field types
                if 'type' in field_def:
                    if field_def['type'] == 'array':
                        if 'structure' in field_def:
                            # Create a model for the array item structure
                            item_model = ResourceYamlMapping._create_nested_model(
                                f"{schema_name}_{field_name.title()}Item",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = List[item_model]
                            fields[field_name] = Field(default_factory=list)
                        else:
                            annotations[field_name] = List[str]
                            fields[field_name] = Field(default_factory=list)
                    elif field_def['type'] == 'object':
                        if 'structure' in field_def:
                            nested_model = ResourceYamlMapping._create_nested_model(
                                f"{schema_name}_{field_name.title()}",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = nested_model
                            fields[field_name] = Field(default_factory=lambda: nested_model())
                        else:
                            annotations[field_name] = Dict[str, Any]
                            fields[field_name] = Field(default_factory=dict)
                else:
                    nested_model = ResourceYamlMapping._create_nested_model(
                        f"{schema_name}_{field_name.title()}",
                        field_def,
                        available_models
                    )
                    annotations[field_name] = nested_model
                    fields[field_name] = Field(default_factory=lambda: nested_model())
            elif field_def == 'array':
                # Simple array type
                annotations[field_name] = List[str]
                fields[field_name] = Field(default_factory=list)
            else:
                # Simple field type - make it required
                field_type = yaml_type_to_python_type(str(field_def), available_models)
                annotations[field_name] = field_type  # Not Optional
                fields[field_name] = Field(...)  # Required field
        
        return type(
            class_name,
            (ResourceField,),
            {
                '__annotations__': annotations,
                **fields
            }
        )

    @staticmethod
    def _create_resource_class(resource_def: dict[str, Any], resource_name: str, available_models: Dict[str, Type[BaseModel]] = None) -> Type[Resource]:
        """Create a Resource subclass from resource definition."""
        # Use the key directly as class name
        class_name = resource_name
        
        # Create field definitions with proper type annotations
        annotations = {
            'service': str,  # Required service field
            'name': str,  # Required name field
            'description': str  # Required description field
        }
        fields = {
            'service': Field(...),  # Required field
            'name': Field(...),  # Required field
            'description': Field(...)  # Required field
        }
        
        # Process resource fields
        resource_fields = resource_def.get('fields', {})
        for field_name, field_def in resource_fields.items():
            if isinstance(field_def, dict):
                # Handle nested field types
                if 'type' in field_def:
                    if field_def['type'] == 'array':
                        if 'structure' in field_def:
                            item_model = ResourceYamlMapping._create_nested_model(
                                f"{resource_name}_{field_name.title()}Item",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = List[item_model]
                            fields[field_name] = Field(default_factory=list)
                        else:
                            annotations[field_name] = List[str]
                            fields[field_name] = Field(default_factory=list)
                    elif field_def['type'] == 'object':
                        if 'structure' in field_def:
                            nested_model = ResourceYamlMapping._create_nested_model(
                                f"{resource_name}_{field_name.title()}",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = nested_model
                            fields[field_name] = Field(default_factory=lambda: nested_model())
                        else:
                            annotations[field_name] = Dict[str, Any]
                            fields[field_name] = Field(default_factory=dict)
                else:
                    nested_model = ResourceYamlMapping._create_nested_model(
                        f"{resource_name}_{field_name.title()}",
                        field_def,
                        available_models
                    )
                    annotations[field_name] = nested_model
                    fields[field_name] = Field(default_factory=lambda: nested_model())
            elif field_def == 'array':
                # Simple array type
                annotations[field_name] = List[str]
                fields[field_name] = Field(default_factory=list)
            else:
                # Simple field type - make it required
                field_type = yaml_type_to_python_type(str(field_def), available_models)
                annotations[field_name] = field_type  # Not Optional
                fields[field_name] = Field(...)  # Required field
        
        model = type(
            class_name,
            (Resource,),
            {
                '__annotations__': annotations,
                **fields
            }
        )
        
        # Add metadata
        model.__description__ = resource_def.get('description', '')
        if 'service' in resource_def:
            model.__service__ = resource_def['service']
        
        return model

    @staticmethod
    def _create_resource_collection_class(collection_def: dict[str, Any], provider_name: str, available_models: Dict[str, Type[BaseModel]] = None) -> Type[ResourceCollection]:
        """Create a ResourceCollection subclass from collection definition."""
        # Use the name field to generate the class name
        class_name = f"{format_class_name(provider_name)}ResourceCollection"
        
        # Create field definitions with proper type annotations
        annotations = {
            'name': str,
            'description': Optional[str],
            'resources': List[Any]  # Will be updated with proper resource types
        }
        fields = {
            'name': Field(default=collection_def.get('name')),
            'description': Field(default=collection_def.get('description')),
            'resources': Field(default_factory=list)
        }
        
        # Process collection fields
        collection_fields = collection_def.get('fields', {})
        for field_name, field_def in collection_fields.items():
            if field_name == 'resources':
                # Skip resources field as it's handled separately
                continue
                
            if isinstance(field_def, dict):
                # Handle nested field types
                if 'type' in field_def:
                    if field_def['type'] == 'array':
                        if 'structure' in field_def:
                            item_model = ResourceYamlMapping._create_nested_model(
                                f"{class_name}_{field_name.title()}Item",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = List[item_model]
                            fields[field_name] = Field(default_factory=list)
                        else:
                            annotations[field_name] = List[str]
                            fields[field_name] = Field(default_factory=list)
                    elif field_def['type'] == 'object':
                        if 'structure' in field_def:
                            nested_model = ResourceYamlMapping._create_nested_model(
                                f"{class_name}_{field_name.title()}",
                                field_def['structure'],
                                available_models
                            )
                            annotations[field_name] = nested_model
                            fields[field_name] = Field(default_factory=lambda: nested_model())
                        else:
                            annotations[field_name] = Dict[str, Any]
                            fields[field_name] = Field(default_factory=dict)
                else:
                    nested_model = ResourceYamlMapping._create_nested_model(
                        f"{class_name}_{field_name.title()}",
                        field_def,
                        available_models
                    )
                    annotations[field_name] = nested_model
                    fields[field_name] = Field(default_factory=lambda: nested_model())
            elif isinstance(field_def, list):
                # Handle resource references
                if all(isinstance(ref, str) for ref in field_def):
                    annotations[field_name] = List[Any]  # Will be updated with proper resource types
                    fields[field_name] = Field(default_factory=list)
            else:
                field_type = yaml_type_to_python_type(str(field_def), available_models)
                annotations[field_name] = Optional[field_type]
                fields[field_name] = Field(default=None)
        
        model = type(
            class_name,
            (ResourceCollection,),
            {
                '__annotations__': annotations,
                **fields
            }
        )
        
        # Add metadata
        model.__description__ = collection_def.get('description', '')
        
        return model

    @classmethod
    def load_yaml(cls, path_or_dict: str | dict) -> Dict[str, 'ResourceYamlMapping']:
        """
        Load resource configuration from a YAML file or dictionary.

        Args:
            path_or_dict: Either a path to a YAML file or a dictionary containing the YAML data

        Returns:
            Dict[str, ResourceYamlMapping]: A dictionary mapping provider names to their resource mappings

        Raises:
            FileNotFoundError: If the YAML file does not exist
            yaml.YAMLError: If the YAML file is invalid
            ValueError: If the input format is invalid
        """
        yaml_data = cls._load_yaml_data(path_or_dict)
        result = {}

        # Process each provider's configuration
        for provider_name, provider_data in yaml_data.items():
            if not isinstance(provider_data, dict):
                continue

            all_nested_schemas = []
            all_resources = []
            collection_class = None
            available_models = {}  # Track created models for cross-references

            # Extract nested schemas - use key directly as class name
            for schema_name, schema_def in provider_data.get('nested_schemas', {}).items():
                schema_class = cls._create_resource_field_class(schema_def, schema_name, available_models)
                all_nested_schemas.append(schema_class)
                available_models[schema_name] = schema_class

            # Extract resources - use key directly as class name
            for resource_name, resource_def in provider_data.get('resources', {}).items():
                resource_class = cls._create_resource_class(resource_def, resource_name, available_models)
                all_resources.append(resource_class)
                available_models[resource_name] = resource_class

            # Extract resource collection - use name field for class name
            collection_data = provider_data.get('resource_collection')
            if collection_data:
                collection_class = cls._create_resource_collection_class(
                    collection_data,
                    collection_data.get('name', provider_name),
                    available_models
                )

            if not collection_class:
                collection_class = ResourceCollection  # Use base class if no custom collection defined

            result[provider_name] = cls(
                nested_schemas=all_nested_schemas,
                resources=all_resources,
                resources_collection=collection_class
            )

        return result
