"""
Utils package for con_mon - contains helper functions and SQL operations.
"""
import os
import yaml
import importlib
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from con_mon_v2.connectors import ConnectorService, ConnectorInput, ConnectorType
from pathlib import Path
from con_mon_v2.resources.models import Resource, ResourceCollection


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

    @classmethod
    def create_fetch_function(
            cls,
            provider_module_path: str,
            method_name: str
    ) -> Callable[
        [ConnectorInput], ResourceCollection]:
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

    @classmethod
    def _create_connector_service_class(
            cls,
            connector_data: dict[str, Any]
    ) -> Type[ConnectorService]:
        """Create a ConnectorService subclass from connector data."""
        provider_service = connector_data.get('provider_service')
        method_name = connector_data.get('method', 'process')
        name = connector_data.get('name')
        
        if not provider_service:
            raise ValueError("provider_service is required in connector configuration")
        if not name:
            raise ValueError("name is required in connector configuration")
            
        fetch_function = cls.create_fetch_function(provider_service, method_name)
        
        # Create a subclass of ConnectorService with proper field definitions
        class_name = f"{name.title()}ConnectorService"
        
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
        class_name = f"{connector_name.title()}ConnectorInput"
        
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


class YamlModel(BaseModel):
    pass


class YamlFieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    LIST = "list"
    ANY = "any"

    @classmethod
    def yaml_field_type_to_python_type(cls, field_type: 'YamlFieldType') -> Type:
        type_mapping = {
            cls.STRING: str,
            cls.INTEGER: int,
            cls.BOOLEAN: bool,
            cls.OBJECT: dict,
            cls.LIST: list,
            cls.ANY: Any
        }
        return type_mapping.get(field_type, Any)


class YamlField(BaseModel):
    name: str
    dtype: YamlFieldType


class YamlModelMapping(BaseModel):
    pydantic_model: Type[Union[YamlModel, Resource, ResourceCollection]]
    fields: List[YamlField]
    is_list: bool = False

    @classmethod
    def create_yaml_model(
            cls,
            name: str,
            annotations: dict,
            fields: dict,
            base_class: Type[BaseModel] = Resource
    ) -> Type[YamlModel]:
        """Create a new Pydantic model type with the given fields."""
        # Create the model class with only YAML-defined fields
        model = type(
            name,
            (base_class,),
            {
                '__annotations__': annotations,
                **fields
            }
        )
        return model

    @classmethod
    def process_yaml_dict(
            cls,
            yaml_data: dict[str, Any],
            parent_name: str = ""
    ) -> tuple[List[YamlField], dict, dict]:
        fields = []
        model_annotations = {}
        model_fields = {}

        for field_name, field_def in yaml_data.items():
            is_field_list = field_name.endswith('[]')
            clean_field_name = field_name[:-2] if is_field_list else field_name

            if isinstance(field_def, str):
                field_type = YamlFieldType(field_def) if field_def in YamlFieldType._value2member_map_ else YamlFieldType.ANY
                yaml_field = YamlField(name=clean_field_name, dtype=YamlFieldType.LIST if is_field_list else field_type)
                fields.append(yaml_field)

                python_type = YamlFieldType.yaml_field_type_to_python_type(yaml_field.dtype)
                if is_field_list:
                    python_type = List[python_type]
                model_annotations[clean_field_name] = python_type
                model_fields[clean_field_name] = Field(default=None)

            elif isinstance(field_def, dict):
                nested_name = f"{parent_name}_{clean_field_name}" if parent_name else clean_field_name
                nested_fields, nested_annotations, nested_field_defs = cls.process_yaml_dict(field_def, nested_name)

                nested_model = cls.create_yaml_model(
                    name=nested_name.title(),
                    annotations=nested_annotations,
                    fields=nested_field_defs
                )

                yaml_field = YamlField(name=clean_field_name, dtype=YamlFieldType.LIST if is_field_list else YamlFieldType.OBJECT)
                fields.append(yaml_field)
                fields.extend(nested_fields)

                if is_field_list:
                    model_annotations[clean_field_name] = List[nested_model]
                else:
                    model_annotations[clean_field_name] = nested_model
                model_fields[clean_field_name] = Field(default_factory=list if is_field_list else nested_model)

        return fields, model_annotations, model_fields

    @classmethod
    def load_yaml(
            cls,
            yaml_dict: dict[str, Any],
    ) -> 'YamlModelMapping':
        model_name = next(iter(yaml_dict))
        fields, model_annotations, model_fields = cls.process_yaml_dict(yaml_dict[model_name])
        is_list = any(field_name.endswith('[]') for field_name in yaml_dict[model_name].keys())
        model_type = cls.create_yaml_model(
            name=model_name,
            annotations=model_annotations,
            fields=model_fields
        )
        return cls(
            pydantic_model=model_type,
            fields=fields,
            is_list=is_list
        )


class ResourceYamlMapping(BaseModel):
    connector_type: str
    resources: List[YamlModelMapping]
    resources_collection: YamlModelMapping

    @staticmethod
    def _load_yaml_data(path_or_dict: str | dict) -> dict:
        """Load YAML data from file path or dict."""
        if isinstance(path_or_dict, (str, Path)):
            with open(path_or_dict, 'r') as f:
                return yaml.safe_load(f)
        return path_or_dict

    @classmethod
    def _process_resource(
            cls,
            resource_name: str,
            resource_def: dict[str, Any]
    ) -> YamlModelMapping:
        """Process a single resource definition."""
        fields_dict = {resource_name: resource_def}
        return YamlModelMapping.load_yaml(fields_dict)

    @classmethod
    def _process_collection(
            cls,
            connector_type: str,
            collection_def: dict[str, Any]
    ) -> YamlModelMapping:
        """Process resource collection definition."""
        collection_name = f"{connector_type.title()}ResourceCollection"
        
        # Create collection model inheriting from ResourceCollection
        fields_dict = {collection_name: collection_def}
        return YamlModelMapping.load_yaml(fields_dict)

    @classmethod
    def load_yaml(
            cls,
            path_or_dict: str | dict
    ) -> Dict[str, 'ResourceYamlMapping']:
        yaml_data = cls._load_yaml_data(path_or_dict)
        result = {}
        for provider_name, provider_data in yaml_data.items():
            if not isinstance(provider_data, dict):
                continue
            resources = []
            for resource_name, resource_def in provider_data.get('resources', {}).items():
                resource_mapping = cls._process_resource(resource_name, resource_def)
                resources.append(resource_mapping)
            collection_data = provider_data.get('resource_collection', {})
            collection_mapping = cls._process_collection(provider_name, collection_data)
            result[provider_name] = cls(
                connector_type=provider_name,
                resources=resources,
                resources_collection=collection_mapping
            )
        return result
